#-*- coding: utf-8 -*-

import sys, glob, os.path, io, re
import logging
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


logger.info("Reading xml from directory: %s" % xmldir)
logger.info("Writing corpusfile in: %s" % corpusfile)

xmlfiles = glob.glob("%s/*.xml" % xmldir)
xmlfiles.sort()

for xmlfile in xmlfiles:
    logger.info("xmlfile: %s" % xmlfile)
    
    #get text and transcription from each word in xml
    #if there is an original_transcription attribute, use that,
    #otherwise the phonemes.
    #Drop silence_tokens, punctuation, etc

    tree = ET.parse(xmlfile)
    root = tree.getroot()
    text = []
    trans = []
    for word in root.findall(".//word"):
        try:
            orth = word.attrib["input_string"]
        except KeyError:
            try:
                orth = word.attrib["string"]
            except KeyError:
                ET.dump(word)
                logger.error("ERROR: no 'input_string' or 'string' found")
                sys.exit(1)
        #| occurs sometimes as joiner for multiword units,
        #but shouldn't be allowed as a word by itself
        #also - and '
        #if re.match(u"^[a-záéíóúA-ZÁÉÍÓÚ0-9'|-]+$", orth):
        if re.match(u"^[a-záéíóúA-ZÁÉÍÓÚ0-9]+(['|-][a-záéíóúA-ZÁÉÍÓÚ0-9'-]+)?$", orth):
            text.append(orth.lower())
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
        logger.warning("WARNING: Empty transcription in %s (text %s, trans %s), not printing line!" % (xmlfile, output_text, output_trans)) 
    else:
        outfh.write(u"%s\t%s\t%s\t%s\t%s\n" % (fileid, speaker, wavfile, output_text, output_trans))

    #sys.exit(1)
