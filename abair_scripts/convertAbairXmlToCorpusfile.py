#-*- coding: utf-8 -*-

import sys, glob, os.path, io, re
import xml.etree.ElementTree as ET

if len(sys.argv) == 5:
    speaker = sys.argv[1]
    xmldir = sys.argv[2]
    wavdir = sys.argv[3]
    corpusfile = sys.argv[4]
else:
    print("USAGE: python convertAbairXmlToCorpusfile.py <speaker> <xmldir> <wavdir> <corpusfile>")
    print("Example: python ../../scripts/convertAbairXmlToCorpusfile.py anb /var/phonetics/Abair_project/Corpora/ga_UL/anb/named-entities/xml/ wav corpusfile.txt")
    sys.exit(1)

outfh = io.open(corpusfile,"w",encoding="utf-8")


print("Reading xml from directory: %s" % xmldir)
print("Writing corpusfile in: %s" % corpusfile)

for xmlfile in glob.glob("%s/*.xml" % xmldir):
    #print("xmlfile: %s" % xmlfile)
    
    #get text and transcription from each word in xml
    #if there is an original_transcription attribute, use that,
    #otherwise the phonemes.
    #Drop silence_tokens, punctuation, etc

    tree = ET.parse(xmlfile)
    root = tree.getroot()
    text = []
    trans = []
    for word in root.findall(".//word"):
        orth = word.attrib["input_string"]
        if re.match(u"^[a-záéíóúA-ZÁÉÍÓÚ0-9'|-]+$", orth):
            text.append(orth)
            if "original_transcription" in word.attrib:
                word_trans = word.attrib["original_transcription"]
                word_trans = re.sub("[012.]", "", word_trans)
                word_trans = re.sub(" +", " ", word_trans)
                word_trans = word_trans.strip()
                trans.append(word_trans)
            else:
                wordtrans = []
                for phn in word.findall(".//phoneme"):
                    wordtrans.append(phn.attrib["symbol"])
                trans.append(" ".join(wordtrans))

    xmlfilebase = os.path.splitext(os.path.basename(xmlfile))[0]
    fileid = "%s_%s" % (speaker,xmlfilebase)
    wavfile = "%s/%s.wav" % (wavdir,xmlfilebase)
    output_text = " ".join(text)
    output_trans = " # ".join(trans)

    if "" in trans:
        print("WARNING: Empty transcription in %s (text %s, trans %s), not printing line!" % (xmlfile, output_text, output_trans)) 
    else:
        outfh.write(u"%s\t%s\t%s\t%s\t%s\n" % (fileid, speaker, wavfile, output_text, output_trans))

    #sys.exit(1)
