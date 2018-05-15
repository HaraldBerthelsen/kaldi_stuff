#-*- coding: utf-8 -*-

import sys, glob, os.path, io, re, requests, json, wave
import logging
import xml.etree.ElementTree as ET

#Suppress annoying info message from urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)

#Set log level 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Use aeneas to split paragraphs into chunks
split_paragraphs = True

#Only needs to be done if timings have changed, or on the first run!
cut_wavfile = True

if len(sys.argv) > 3:
    corpus_base = sys.argv[1]
    audio_base = sys.argv[2]
    xmlfiles = sys.argv[3:]
else:
    print("USAGE: python convertTeiXmlToCorpusfile.py <corpus_base> <audio_base> <teitok xml files>")
    print("Example: python scripts/abair_scripts/convertTeiXmlToCorpusfile.py data audio xml/*.xml")
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

        #remove accents and syllable boundaries
        transcription = re.sub("[012.]","",transcription)
        transcription = re.sub(" +"," ",transcription)
        transcription = transcription.strip()

        #uncertain word, transcription should be "spn"
        if orth == "spn":
            transcription = "spn"


        
        trans.append(transcription)
        i += 1
    return trans

#xmlfiles = glob.glob("%s/xml/*.xml" % teitok_dir)
#xmlfiles.sort()
for xmlfile in xmlfiles:
    logger.info("Reading tei xml file: %s" % xmlfile)
    basename = os.path.splitext(os.path.basename(xmlfile))[0]
    logger.debug("basename: %s" % basename)



    #make sure wavfile is there
    teitok_dir = "%s/.." % os.path.dirname(xmlfile)
    print(teitok_dir)
    wavfilename = "%s/wav/%s.wav" % (teitok_dir, basename)
    if not os.path.isfile(wavfilename):
        logger.error("ERROR: wavfile %s is missing" % wavfilename)
        sys.exit(1)
    else:
        logger.debug("wavfile: %s" % wavfilename)

    #parse xml
    tree = ET.parse(xmlfile)
    root = tree.getroot()

    #Look for "scribe" tag, and don't process if scribe is AUTO
    try:
        scribe = root.find(".//Trans").attrib["scribe"]
        logger.info("scribe: %s" % scribe)
        if scribe == "AUTO":
            logger.warning("xmlfile %s - scribe: %s, SKIPPING" % (xmlfile,scribe))
            continue
    except Exception as e:
        logger.error("Couldn't find scribe in %s, reason:\n%s" % (xmlfile,e))
        continue


    
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
        tokens = u.findall(".//tok")
        if len(tokens) == 0:
            continue
        for tok in tokens:
            #if tok.text and tok.text != "xxx" and re.match("^[a-záéíóúA-ZÁÉÍÓÚ]+$", tok.text):
            #The regexp drops tokens with punctuation, and mwu-s
            if tok.text and re.match("^[a-záéíóúA-ZÁÉÍÓÚ,.!?#'-]+$", tok.text):
                text = tok.text.lower()


                #fix some other issues
                text = re.sub("^'","", text)
                text = re.sub("^mwu#","", text)
                text = re.sub("^-","", text)
                text = re.sub("-$","", text)

                #replace uncertain words with "spn" (also needed in output from ltsserver)
                if "xxx" in text:
                    text = "spn"
                
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

    #If there is punctuation in the text, use aeneas to split it into chunks
    if split_paragraphs:
        for textid in sorted(texts.keys()):
            spkr = texts[textid]["name"]
            start = texts[textid]["start"]
            end = texts[textid]["end"]
            text = texts[textid]["text"]
            if re.search("[,.!?]", " ".join(text)):
                try:
                    logger.info(u"FOUND PUNCTUATION IN: %s\t%s\t%s\t%s\t%s" % (spkr,textid,start,end," ".join(text)))
                    #First check that the soundfile is actually this long
                    #If it isn't, that means there is a problem with the xml markup..
                    wf = wave.open(wavfilename,'r')
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    wf.close()
                    duration = frames / float(rate)

                    if start > duration:
                        msg = "Textid %s has starttime %f, but wavfile is only %f. SKIPPING" % (textid, start, duration)
                        del texts[textid]
                        logger.warning(msg)
                        raise Exception(msg)
                        

                    
                    #make a temporary cut wavfile with this part of the main wavfile
                    tmp_wavfile = "/tmp/%s.wav" % textid
                    sox_command = "sox %s -r 16000 -c 1 %s trim %f %f" % (wavfilename, tmp_wavfile, start, end-start)
                    logger.info(sox_command)
                    os.system(sox_command)

                    #split text on punctuation, write each chunk to one line of temporary text file
                    tmpchunks = re.split("[,.!?]", " ".join(text))
                    chunks = []
                    for chunk in tmpchunks:
                        if not re.match("^\s*$", chunk):
                            chunks.append(chunk)


                    tmp_txtfile = "/tmp/%s.txt" % textid
                    fh = io.open(tmp_txtfile, "w", encoding="utf-8")
                    fh.write("\n".join(chunks))
                    fh.close()

                    #call aeneas with temp files, output in temporary json file
                    tmp_jsonfile = "/tmp/%s.json" % textid
                    aeneas_config = "task_language=ga|os_task_file_format=json|is_text_type=plain|task_adjust_boundary_algorithm=percent|task_adjust_boundary_percent_value=50"
                    run_aeneas_cmd = 'python -m aeneas.tools.execute_task "%s" %s "%s" %s' % (tmp_wavfile,  tmp_txtfile, aeneas_config, tmp_jsonfile)

                    logger.info(run_aeneas_cmd)
                    
                    os.system(run_aeneas_cmd)

                    #read json file, create new textids, remove original textid
                    timings = json.loads(open(tmp_jsonfile).read())
                    fragments = timings["fragments"]

                    i = 0
                    while i < len(fragments):
                        fragment = fragments[i]

                        logger.debug(fragment["begin"])
                        logger.debug(fragment["end"])
                        ftext = "".join(fragment["lines"])
                        logger.debug(ftext)

                        i += 1

                        chunkid = "%s_%03d" % (textid,i)
                        texts[chunkid] = {
                            "name":spkr,
                            "start":start+float(fragment["begin"]),
                            "end":start+float(fragment["end"]),
                            "text":ftext.split(" "),
                            "trans":[]
                        }
                    del texts[textid]
                except Exception as e:
                    logger.error("Failed to split paragraph %s\nTEXT: %s\nERROR MESSAGE: %s" % (textid," ".join(text),e))
                    #sys.exit()
        
        

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

            if end-start > 0:        
                sox_command = "sox %s -r 16000 -c 1 %s trim %f %f" % (wavfilename, new_wavfile, start, end-start)
                logger.info(sox_command)
                os.system(sox_command)
            else:
                logger.warning("Textid %s is zero length (or less). SKIPPING." % textid)
                del texts[textid]
            #sys.exit()
        
    #add transcription
    for textid in sorted(texts.keys()):
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

            if "" in trans:
                logger.info("Found empty trans, trying to repair")
                i = 0
                while i < len(trans):
                    if trans[i] == "":
                        trans[i] = "spn"
                    i += 1

            
            if "" in trans or trans == []:
                logger.warning("WARNING: Empty transcription in %s (text %s, trans %s), not printing line!" % (xmlfile, output_text, output_trans)) 
            else:
                output_text = " ".join(text)
                output_trans = " # ".join(trans)
                corpus_line = u"%s\t%s\t%s\t%s\t%s\n" % (textid, speaker_name, wavfile, output_text, output_trans)
                #logger.debug("Corpus line: %s" % corpus_line)
                outfh.write(corpus_line)

        outfh.close()
