#-*- coding: utf-8 -*-

import sys, glob, os.path, io, re, requests, json
import logging
import xml.etree.ElementTree as ET

#Suppress annoying info message from urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)

#Set log level 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#Only needs to be done if timings have changed, or on the first run!
cut_wavfile = False

if len(sys.argv) == 4:
    teitok_dir = sys.argv[1]
    corpus_base = sys.argv[2]
    audio_base = sys.argv[3]
else:
    print("USAGE: python convertTeiXmlToCorpusfile.py <teitok_dir> <corpus_base> <audio_base>")
    print("Example: python scripts/abair_scripts/convertTeiXmlToCorpusfile.py teitok_comhra_test data audio")
    sys.exit(1)


def getTrans(dialect,text):
    if dialect in ["connacht", "ros muc"]:
        serverdialect = "ga_CM"            
    elif dialect in ["kerry", "munster", "imunster"]:
        serverdialect = "ga_MU"            
    elif dialect in ["ulster"]:
        serverdialect = "ga_GD"            
    elif dialect in ["uncertain", "?"]:
        serverdialect = "ga_CM"            
    else:
        logger.warning("No way implemented of getting transcription for \"%s\" accent, using 'ga_CM'" % accent)
        serverdialect = "ga_CM"            
        #sys.exit(1)


    logger.debug("Transcribing: %s" % text)
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

        #remove accents and syllable boundaries
        transcription = re.sub("[012.]","",transcription)
        transcription = re.sub(" +"," ",transcription)
        transcription = transcription.strip()

        trans.append(transcription)
        i += 1
    return trans

xmlfiles = glob.glob("%s/xml/*.xml" % teitok_dir)
xmlfiles.sort()
for xmlfile in xmlfiles:
    logger.info("Reading tei xml file: %s" % xmlfile)
    basename = os.path.splitext(os.path.basename(xmlfile))[0]
    logger.debug("basename: %s" % basename)



    #make sure wavfile is there
    wavfilename = "%s/wav/%s.wav" % (teitok_dir, basename)
    if not os.path.isfile(wavfilename):
        logger.error("ERROR: wavfile %s is missing" % wavfilename)
        sys.exit(1)
    else:
        logger.debug("wavfile: %s" % wavfilename)

    #parse xml
    tree = ET.parse(xmlfile)
    root = tree.getroot()

    #create speaker names and add to spk2gender file
    speakers = {}
    for person in root.findall(".//person"):
        speaker_id = person.attrib["id"]
        output_speaker_id = "%s_%s" % (basename, speaker_id)
        try:
            accent = person.findall("accent")[0].text.lower()
        except:
            accent = "?"
        gender = person.findall("gender")[0].text.lower()
        speakers[speaker_id] = {"name":output_speaker_id,"accent":accent, "gender":gender}

    spk2gender = {}
    spk2gender_file = "%s/spk2gender" % corpus_base
    try:
        spk2gender_fh = io.open(spk2gender_file,"r",encoding="utf-8")
        for line in spk2gender_fh.readlines():
            (spk,gender) = line.strip().split("\t")
            spk2gender[spk] = gender
        spk2gender_fh.close()
    except:
        logger.info("spk2gender file %s not found, creating it" % spk2gender_file)

    for speaker in speakers:
        logger.debug("%s\t%s" % (speaker, speakers[speaker]))
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
        uid = int(re.sub(r"u-?",r"", u.attrib["id"]))

        #skip overlapping speech
        if "Overlap" in who:
            continue

        speaker_name = speakers[who]["name"]

        words = []
        tokens = u.findall("tok")
        if len(tokens) == 0:
            continue
        for tok in tokens:
            #if tok.text and tok.text != "xxx" and re.match("^[a-záéíóúA-ZÁÉÍÓÚ]+$", tok.text):
            #The regexp drops tokens with punctuation, and mwu-s
            if tok.text and "xxx" not in tok.text and re.match("^[a-záéíóúA-ZÁÉÍÓÚ,.!?#'-]+$", tok.text):
                text = tok.text.lower()
                text = re.sub("[,.!?]","", text)
                text = re.sub("^'","", text)
                text = re.sub("^mwu#","", text)
                text = re.sub("^-","", text)
                text = re.sub("-$","", text)
                #text = re.sub("#"," ", text)
                text = text.strip()
                if text != "":
                    if "#" in text:
                        #multi-word unit
                        words.extend(text.split("#"))
                    else:
                        words.append(text)

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
    if cut_wavfile:
        for textid in sorted(texts.keys()):
            spkr = texts[textid]["name"]
            start = texts[textid]["start"]
            end = texts[textid]["end"]
            text = texts[textid]["text"]
            logger.info(u"%s\t%s\t%s\t%s\t%s" % (spkr,textid,start,end," ".join(text)))

            speaker_name = speakers[spkr]["name"]
            corpuswavdir = "%s/%s/wav" % (audio_base,speaker_name)

            if not os.path.exists(corpuswavdir):
                logger.info("NOTE: wav dir %s not found, creating it." % corpuswavdir)
                os.makedirs(corpuswavdir)

            new_wavfile = "%s/%s.wav" % (corpuswavdir,textid)

            sox_command = "sox %s -r 16000 -c 1 %s trim %f %f" % (wavfilename, new_wavfile, start, end-start)
            logger.info(sox_command)
            os.system(sox_command)
            #sys.exit()
        
    #add transcription
    for textid in texts.keys():
        spkr = texts[textid]["name"]
        text = texts[textid]["text"]
        trans = texts[textid]["trans"]

        accent = speakers[spkr]["accent"]
        logger.debug("Getting transcription for \"%s\" accent" % accent)
        logger.debug("Text: %s" % " ".join(text))
        transcription = getTrans(accent, " ".join(text))

        logger.debug("Trans: %s" % transcription)

        if len(text) != len(transcription):
            logger.error("ERROR: text and trans are not equal length (%d, %d)\n%s\n%s" % (len(text),len(transcription)," ".join(text)," # ".join(transcription)))
            i = 0
            while i < len(text) and i < len(transcription):
                print("%s\t%s" % (text[i], transcription[i]))
                i += 1
            #sys.exit()
            texts[textid]["trans"] = []   
        else:
            texts[textid]["trans"] = transcription

        logger.debug("%s\t%s" % (textid, texts[textid]))


    #sort texts by speaker
    texts_by_speaker = {}
    for textid in sorted(texts.keys()):
        speaker = texts[textid]["name"]
        speaker_name = speakers[speaker]["name"]
        if speaker_name in texts_by_speaker:
            texts_by_speaker[speaker_name].append(textid)
        else:
            texts_by_speaker[speaker_name] = [textid]

    #write corpusfile for each speaker
    for speaker_name in sorted(texts_by_speaker.keys()):

        #create corpusfile
        corpusdir = "%s/%s" % (corpus_base,speaker_name)
        corpusfile = "%s/corpusfile.txt" % corpusdir
        logger.debug("Creating corpusfile %s" % corpusfile)
        if not os.path.exists(corpusdir):
            logger.info("NOTE: corpus dir %s not found, creating it." % corpusdir)
            os.makedirs(corpusdir)
            #empty existing corpusfile
        outfh = io.open(corpusfile,"w",encoding="utf-8")
        outfh.close()
        ##end

        logger.info("Writing to corpusfile %s" % corpusfile)
        outfh = io.open(corpusfile,"w",encoding="utf-8")
        for textid in texts_by_speaker[speaker_name]:
            text = texts[textid]["text"]
            trans = texts[textid]["trans"]

            wavfile = "../../%s/%s/wav/%s.wav" % (audio_base,speaker_name,textid)
            output_text = " ".join(text)
            output_trans = " # ".join(trans)
        
            if "" in trans or trans == []:
                logger.warning("WARNING: Empty transcription in %s (text %s, trans %s), not printing line!" % (xmlfile, output_text, output_trans)) 
            else:
                corpus_line = u"%s\t%s\t%s\t%s\t%s\n" % (textid, speaker_name, wavfile, output_text, output_trans)
                logger.debug("Corpus line: %s" % corpus_line)
                outfh.write(corpus_line)

        outfh.close()
