#-*- coding: utf-8 -*-

import sys, glob, os.path, io, re, requests, json
import logging
import xml.etree.ElementTree as ET

#Suppress annoying info message from urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


if len(sys.argv) == 3:
    teitok_dir = sys.argv[1]
    corpus_base = sys.argv[2]
else:
    print("USAGE: python convertTeiXmlToCorpusfile.py <teitok_dir> <corpus_base>")
    print("Example: python scripts/abair_scripts/convertTeiXmlToCorpusfile.py teitok_comhra_test data")
    sys.exit(1)


def getTrans(dialect,text):
    if dialect == "connacht":
        serverdialect = "ga_CM"            
    else:
        logger.error("ERROR: no way implemented of getting transcription for \"%s\" accent" % accent)
        sys.exit(1)


    logger.info("Transcribing: %s" % text)
    headers = {"Content-type": "application/json", "Accept": "text/plain", "Connection":"keep-alive"}
    data = {
        "input": text,
        "locale": serverdialect,
        "postlex": "no",
        "format":"json"
    }

    host = "http://localhost"
    port = "2029"

    logger.debug("Sending: %s" % json.dumps(data))

    r = requests.post("%s:%s/transcription" % (host,port), headers=headers, data=json.dumps(data))


    jsonitems = r.json().split("\n")
    logger.debug("REPLY: %s" % jsonitems)
    logger.debug("REPLY contains %d items" % len(jsonitems))

    #remove empty lines in json
    tmp = []
    for item in jsonitems:
        if item != "":
            tmp.append(item)
    jsonitems = tmp

    ############################

    #The server always sends . even if it's not in the input
    #punctuation but not ,' or -
    lastitem = json.loads(jsonitems[-1])
    #lastitem = jsonitems[-1]
    if re.search("[^.?!:]$", text) and lastitem["Item"]["Type"] == "Punctuation":
        logger.debug("Text does not end with punctuation: \"%s\", but last jsonitem is %s. Last jsonitem removed!" % (text, lastitem))
        jsonitems = jsonitems[0:-1]

    ##############################



    i = 0
    trans = []
    while i < len(jsonitems):
        jsonitem = jsonitems[i]

        if jsonitem == "":
            continue

        #print("JSON ITEM: %s" % jsonitem)
        item = json.loads(jsonitem)
        #item = jsonitem
        #print("ITEM: %s" % item)

        orth = item['Item']['Word']
        transcription = item['Item']['Transcription']
        trans.append(transcription)
        i += 1
    return trans


for xmlfile in glob.glob("%s/*.xml" % teitok_dir):
    logger.info("Reading tei xml file: %s" % xmlfile)
    basename = os.path.splitext(os.path.basename(xmlfile))[0]
    logger.info("basename: %s" % basename)



    #make sure wavfile is there
    wavfilename = "%s/%s.wav" % (teitok_dir, basename)
    if not os.path.isfile(wavfilename):
        logger.error("ERROR: wavfile %s is missing" % wavfilename)
        sys.exit(1)
    else:
        logger.info("wavfile: %s" % wavfilename)

    #parse xml
    tree = ET.parse(xmlfile)
    root = tree.getroot()

    #create speaker names and add to spk2gender file
    speakers = {}
    for person in root.findall(".//person"):
        speaker_id = person.attrib["id"]
        output_speaker_id = "%s_%s" % (basename, speaker_id)
        accent = person.findall("accent")[0].text.lower()
        gender = person.findall("gender")[0].text.lower()
        speakers[speaker_id] = {"name":output_speaker_id,"accent":accent, "gender":gender}

    spk2gender_file = "%s/spk2gender" % corpus_base
    spk2gender_fh = io.open(spk2gender_file,"r",encoding="utf-8")
    spk2gender = {}
    for line in spk2gender_fh.readlines():
        (spk,gender) = line.strip().split("\t")
        spk2gender[spk] = gender
    spk2gender_fh.close()

    for speaker in speakers:
        logger.info("%s\t%s" % (speaker, speakers[speaker]))
        #create corpusfile
        speaker_name = speakers[speaker]["name"]
        corpusfile = "%s/%s/corpusfile.txt" % (corpus_base,speaker_name)
        logger.debug("Creating corpusfile %s" % corpusfile)
        outfh = io.open(corpusfile,"w",encoding="utf-8")
        outfh.close()

        #check if speaker is in spk2gender
        if speakers[speaker]["name"] not in spk2gender:
            logger.info("NOTE: Adding following line to the spk2gender file:\n%s %s" % (speakers[speaker]["name"], speakers[speaker]["gender"]))
            spk2gender[speakers[speaker]["name"]] = speakers[speaker]["gender"]
        
    spk2gender_fh = io.open(spk2gender_file,"w",encoding="utf-8")
    for speaker in sorted(spk2gender.keys()):
        spk2gender_fh.write(u"%s\t%s\n" % (speaker, spk2gender[speaker]))
    spk2gender_fh.close()


    #get text, starttime, endtime
    texts = {}
    for u in root.findall(".//u"):
        if "who" not in u.attrib:
            continue
        who = u.attrib["who"]
        start = float(u.attrib["start"])
        end = float(u.attrib["end"])
        uid = int(u.attrib["id"].replace("u-",""))

        speaker_name = speakers[who]["name"]

        words = []
        tokens = u.findall("tok")
        if len(tokens) == 0:
            continue
        for tok in tokens:
            if tok.text and tok.text != "xxx" and re.match("^[a-záéíóúA-ZÁÉÍÓÚ]+$", tok.text):
                words.append(tok.text)
        if len(words) == 0:
            continue

        textid = "%s_%04d" % (speaker_name,uid)
        texts[textid] = {
            "name":who, 
            "start":start, 
            "end":end, 
            "text":words, 
            "trans":[]
        }
        

    #cut wavfile
    for textid in texts.keys():
        spkr = texts[textid]["name"]
        start = texts[textid]["start"]
        end = texts[textid]["end"]
        text = texts[textid]["text"]
        logger.info(u"%s\t%s\t%s\t%s\t%s" % (spkr,textid,start,end," ".join(text)))

        corpuswavdir = "%s/%s/wav" % (corpus_base,speaker_name)

        if not os.path.exists(corpuswavdir):
            logger.info("NOTE: wav dir %s not found, creating it." % corpuswavdir)
            os.makedirs(corpuswavdir)

        new_wavfile = "%s/%s.wav" % (corpuswavdir,textid)

        sox_command = "sox %s -r 16000 %s trim %f %f" % (wavfilename, new_wavfile, start, end-start)
        logger.info(sox_command)
        #os.system(sox_command)
        
    #add transcription
    for textid in texts.keys():
        spkr = texts[textid]["name"]
        text = texts[textid]["text"]
        trans = texts[textid]["trans"]

        accent = speakers[spkr]["accent"]
        logger.info("Getting transcription for \"%s\" accent" % accent)
        logger.info("Text: %s" % " ".join(text))
        transcription = getTrans(accent, " ".join(text))
        logger.info("Trans: %s" % transcription)

        if len(text) != len(transcription):
            logger.error("ERROR: text and trans are not equal length (%d, %d)\n%s\n%s" % (len(text),len(transcription)," ".join(text)," # ".join(transcription)))
            i = 0
            while i < len(text):
                print("%s\t%s" % (text[i], transcription[i]))
                i += 1
                
        else:
            texts[textid]["trans"] = transcription

        logger.info("%s\t%s" % (textid, texts[textid]))
        #sys.exit()


    #write corpusfile

    for textid in sorted(texts.keys()):
        spkr = texts[textid]["name"]
        text = texts[textid]["text"]
        trans = texts[textid]["trans"]

        speaker_name = speakers[spkr]["name"]
        corpusfile = "%s/%s/corpusfile.txt" % (corpus_base,speaker_name)

        logger.debug("Writing to corpusfile %s" % corpusfile)

        outfh = io.open(corpusfile,"a",encoding="utf-8")

        wavfile = "wav/%s.wav" % textid
        output_text = " ".join(text)
        output_trans = " # ".join(trans)
        
        if "" in trans:
            logger.warning("WARNING: Empty transcription in %s (text %s, trans %s), not printing line!" % (xmlfile, output_text, output_trans)) 
        else:
            corpus_line = u"%s\t%s\t%s\t%s\t%s\n" % (textid, speaker_name, wavfile, output_text, output_trans)
            logger.debug("Corpus line: %s" % corpus_line)
            outfh.write(corpus_line)

        outfh.close()
