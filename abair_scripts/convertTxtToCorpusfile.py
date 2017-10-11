#-*- coding: utf-8 -*-

import sys, glob, os.path, io, re, requests, json
import logging
import xml.etree.ElementTree as ET

#Suppress annoying info message from urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


if len(sys.argv) == 3:
    text_dir = sys.argv[1]
    corpus_base = sys.argv[2]
else:
    print("USAGE: python convertTxtToCorpusfile.py <text_dir> <corpus_base>")
    print("Example: python scripts/abair_scripts/convertTxtToCorpusfile.py ~/svn/Corpora/ga_UL/seanchas_rann_na_feirste/corpus /media/Data/RecognitionData/data")
    sys.exit(1)


def getTrans(dialect,text):
    if dialect == "connacht":
        serverdialect = "ga_CM"            
    elif dialect == "donegal":
        serverdialect = "ga_GD"            
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
    if re.search("[^,.?!:-]$", text) and lastitem["Item"]["Type"] == "Punctuation":
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

txtfiles = glob.glob("%s/txt/*.txt" % text_dir)
txtfiles.sort()

for txtfile in txtfiles:
    logger.info("Reading text file: %s" % txtfile)
    basename = os.path.splitext(os.path.basename(txtfile))[0]
    logger.info("basename: %s" % basename)



    #make sure wavfile is there
    wavfilename = "%s/wav/%s.wav" % (text_dir, basename)
    if not os.path.isfile(wavfilename):
        logger.error("ERROR: wavfile %s is missing" % wavfilename)
        sys.exit(1)
    else:
        logger.info("wavfile: %s" % wavfilename)

    #find speaker names and add to spk2gender file
    spk2gender_file = "%s/spk2gender" % corpus_base
    spk2gender = {}
    try:
        spk2gender_fh = io.open(spk2gender_file,"r",encoding="utf-8")
        for line in spk2gender_fh.readlines():
            (spk,gender) = line.strip().split("\t")
            spk2gender[spk] = gender
        spk2gender_fh.close()
    except IOError:
        print("spk2gender file %s not found, creating it.." % spk2gender_file)

    #This assumes that speaker is the last part of filename before sentnr
    m = re.search("_([^_]+)_[0-9]+$", basename)
    speaker = m.group(1)    
    logger.info("Speaker: %s" % (speaker))


    #create corpusfile
    corpusprefix = "seanchas_rann_na_feirste"
    speaker_name =  "%s_%s" % (corpusprefix, speaker)
    corpusdir = "%s/%s" % (corpus_base,speaker_name)
    corpusfile = "%s/corpusfile.txt" % corpusdir

    if not os.path.exists(corpusdir):
        logger.info("NOTE: corpus dir %s not found, creating it." % corpusdir)
        os.makedirs(corpusdir)
        outfh = io.open(corpusfile,"w",encoding="utf-8")
        outfh.close()

    #check if speaker is in spk2gender
    if speaker not in spk2gender:
        #Assumes last char is m|f
        gender = speaker[-1]
        logger.info("NOTE: Adding following line to the spk2gender file:\n%s %s" % (speaker, gender))
        spk2gender[speaker] = gender
        
    spk2gender_fh = io.open(spk2gender_file,"w",encoding="utf-8")
    for speaker in sorted(spk2gender.keys()):
        spk2gender_fh.write(u"%s\t%s\n" % (speaker, spk2gender[speaker]))
    spk2gender_fh.close()

    #get text
    txt_fh = io.open(txtfile,"r",encoding="utf-8")
    text = txt_fh.read().strip().split(" ")
    txt_fh.close()

    accent = "donegal"
        
    #add transcription
    
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
        continue
                

    #write corpusfile
    logger.debug("Writing to corpusfile %s" % corpusfile)

    outfh = io.open(corpusfile,"a",encoding="utf-8")

    wavfile = "wav/%s.wav" % basename
    output_text = " ".join(text)
    output_trans = " # ".join(transcription)
        
    if "" in transcription:
        logger.warning("WARNING: Empty transcription in %s (text %s, trans %s), not printing line!" % (txtfile, output_text, output_trans)) 
    else:
        corpus_line = u"%s\t%s\t%s\t%s\t%s\n" % (basename, speaker_name, wavfile, output_text, output_trans)
        logger.debug("Corpus line: %s" % corpus_line)
        outfh.write(corpus_line)

    outfh.close()
    #sys.exit()
