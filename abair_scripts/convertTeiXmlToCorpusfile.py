#-*- coding: utf-8 -*-

import sys, glob, os.path, io, re, requests, json
import xml.etree.ElementTree as ET

if len(sys.argv) == 3:
    xmldir = sys.argv[1]
    corpus_base = sys.argv[2]
else:
    print("USAGE: python convertTeiXmlToCorpusfile.py <xmldir> <corpus_base>")
    print("Example: python scripts/abair_scripts/convertTeiToCorpusfile.py teitok_comhra data")
    sys.exit(1)


def getTrans(dialect,text):
    print("Transcribing: %s" % text)
    headers = {"Content-type": "application/json", "Accept": "text/plain", "Connection":"keep-alive"}
    data = {
        "input": text,
        "locale": dialect,
        "postlex": "no",
        "format":"json"
    }

    host = "http://localhost"
    port = "2029"

    r = requests.post("%s:%s/transcription" % (host,port), headers=headers, data=json.dumps(data))


    jsonitems = r.json().split("\n")
    #print("REPLY: %s" % jsonitems)
    #print("REPLY contains %d items" % len(jsonitems))

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
        print("Text does not end with punctuation: \"%s\", but last jsonitem is %s. Last jsonitem removed!" % (text, lastitem))
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



for xmlfile in glob.glob("%s/*.xml" % xmldir):
    print("Reading tei xml file: %s" % xmlfile)
    basename = os.path.splitext(os.path.basename(xmlfile))[0]
    print("basename: %s" % basename)

    #make sure wavfile is there
    wavfilename = "%s.wav" % basename
    if not os.path.isfile(wavfilename):
        print("ERROR: wavfile %s is missing")
        sys.exit(1)
    else:
        print("wavfile: %s" % wavfilename)

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
        print("%s\t%s" % (speaker, speakers[speaker]))
        #check if speaker is in spk2gender
        if speakers[speaker]["name"] not in spk2gender:
            print("NOTE: Adding following line to the spk2gender file:\n%s %s" % (speakers[speaker]["name"], speakers[speaker]["gender"]))
            spk2gender[speakers[speaker]["name"]] = speakers[speaker]["gender"]
        
    spk2gender_fh = io.open(spk2gender_file,"w",encoding="utf-8")
    for speaker in sorted(spk2gender.keys()):
        spk2gender_fh.write(u"%s\t%s\n" % (speaker, spk2gender[speaker]))
    spk2gender_fh.close()


    #get text, starttime, endtime
    texts = []
    for u in root.findall(".//u"):
        if "who" not in u.attrib:
            continue
        who = u.attrib["who"]
        start = float(u.attrib["start"])
        end = float(u.attrib["end"])
        uid = u.attrib["id"]

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

        textid = "%s_%s" % (speaker_name,uid)
        texts.append((who, textid, start, end, words))        

    #cut wavfile
    for (spkr,textid,start,end,text) in texts:
        print(u"%s\t%s\t%s\t%s\t%s" % (spkr,textid,start,end," ".join(text)))

        speaker_name = speakers[who]["name"]
        new_wavdir = "%s/%s" % (corpus_base,speaker_name)

        if not os.path.exists(new_wavdir):
            print("NOTE: wav dir %s not found, creating it." % new_wavdir)
            os.makedirs(new_wavdir)
            os.makedirs(new_wavdir+"/wav")

        new_wavfile = "%s/wav/%s.wav" % (new_wavdir,textid)

        sox_command = "sox %s -r 16000 %s trim %f %f" % (wavfilename, new_wavfile, start, end-start)
        print(sox_command)
        #os.system(sox_command)
        
    #add transcription
    for (spkr,_,_,_,text) in texts:
        accent = speakers[spkr]["accent"]
        if accent == "connacht":
            print("Getting transcription for \"%s\" accent" % accent)
            trans = getTrans("ga_CM", " ".join(text))
            print("Trans: %s" % trans)

            if len(text) != len(trans):
                print("ERROR: text and trans are not equal length (%d, %d)\n%s\n%s" % (len(text),len(trans)," ".join(text)," # ".join(trans)))
                i = 0
                while i < len(text):
                    print("%s\t%s" % (text[i], trans[i]))
                    i += 1
                

            
        else:
            print("ERROR: no way implemented of getting transcription for \"%s\" accent" % accent)

    #write corpusfile
        
