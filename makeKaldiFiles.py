#-*- coding: utf-8 -*-
import sys, os, io, re, wave

#Using corpusfiles to setup kaldi.

#input:
#experiment dir (in kaldi/egs)
#spk2gender file
#a list of corpusfiles 
#how to split into train|test

#output:
#<exp>/data/local/corpus.txt
#<exp>/data/local/dict/lexicon.txt, nonsilence_phones.txt, silence_phones.txt, optional_silence.txt
#<exp>/data/<train|test>/spk2gender, utt2spk, wav.scp, text


#default settings for kaldibase, spk2gender_file, split_method
#TODO allow setting these with command line options

kaldi_base = "/home/harald/git/kaldi/egs"
spk2gender_file = "./spk2gender"
split_method = "random_percentage" #random_percentage, random_number, corpusfile, speaker, list ..
test_percentage = "2"

exit_on_first_error = True
exit_on_file_error = True

usage = "Usage: python makeKaldiFiles.py <experiment-directory> <corpusfile1> .. <corpusfileN>\nExample: python ../kaldi_stuff/makeKaldiFiles.py irish_named_entities_test *_named_entities/corpusfile.txt"

spk2gender_dict = {}

def main(kaldi_base, expdir, corpusfiles):

    print("Exp dir: %s\nspk2gender file: %s\nCorpusfiles: %s" % (expdir, spk2gender_file, corpusfiles))

    #check that kaldi_base exists and is writable
    if os.access(kaldi_base, os.W_OK):
        print("Kaldi base %s is ok" % kaldi_base)
    else:
        if not os.path.isdir(kaldi_base):
            print("Kaldi base %s doesn't exist" % kaldi_base)
        else:
            print("You don't have permission to write to kaldi base %s" % kaldi_base)

    #validate spk2gender file
    if os.path.isfile(spk2gender_file):
        if validate_spk2gender_file(spk2gender_file):
            print("spk2gender file %s is OK" % spk2gender_file)
        elif exit_on_file_error:
            print("Error in spk2gender file %s" % spk2gender_file)
            sys.exit(1)
    else:
        print("spk2gender file %s doesn't exist" % spk2gender_file)

    #validate the corpusfiles
    for corpusfile in corpusfiles:
        if os.path.isfile(corpusfile):
            if validate_corpusfile(corpusfile):
                print("corpusfile %s is OK" % corpusfile)
            elif exit_on_file_error:
                print("Error in corpusfile %s" % corpusfile)
                sys.exit(1)
        else:
            print("corpus file %s doesn't exist" % corpusfile)

    #Write language files 
    #<exp>/data/local/corpus.txt
    #<exp>/data/local/dict/lexicon.txt, nonsilence_phones.txt, silence_phones.txt, optional_silence.txt
    writeLanguageFiles(expdir,corpusfiles)
    #Split train/test
    (train,test) = splitTrainTest(corpusfiles)
    #Write train/test files
    #<exp>/data/<train|test>/spk2gender, utt2spk, wav.scp, text
    writeDataFiles(expdir, "train", train)
    writeDataFiles(expdir, "test", test)

def validate_spk2gender_file(spk2gender_file):
   fh = io.open(spk2gender_file,"r",encoding="utf-8")
   lines = fh.readlines()
   linenr = 0
   ok = True
   for line in lines:
       line = line.strip()
       linenr += 1
       regexp = "^([a-z_]+)\t([mf])$"
       m = re.match(regexp, line)
       if m:
           spk2gender_dict[m.group(1)] = m.group(2)
       else:
           print("Error in %s line %d (doesn't match regexp \"%s\": %s" % (spk2gender_file, linenr, regexp, line))
           ok = False
           if exit_on_first_error:
               sys.exit(1)
   return ok
           
 
def validate_corpusfile(corpusfile):
   fh = io.open(corpusfile,"r",encoding="utf-8")
   lines = fh.readlines()
   linenr = 0
   ok = True
   for line in lines:
       line = line.strip()
       linenr += 1

       #definition of fields
       speaker_re = u"[a-z]+"
       fileid_re = u"%s_[a-zA-Z0-9_-]+" % speaker_re
       wavfile_re = u"[a-zA-Z0-9_/-]+.wav"
       text_re = u"[a-záéíóú0-9 '|-]+"
       trans_re = u"[a-z@# _]+"

       regexp = "^(%s)\t(%s)\t(%s)\t(%s)\t(%s)$" % (fileid_re,speaker_re,wavfile_re,text_re,trans_re)
       m = re.match(regexp, line)
       if not m:
           print(u"Error in %s line %d (doesn't match regexp \"%s\": %s" % (corpusfile, linenr, regexp, line))
           ok = False
           if exit_on_first_error:
               sys.exit(1)
       else:
       #check that speaker is in spk2gender file
           speaker = m.group(2)
           if speaker not in spk2gender_dict:
               print("ERROR: speaker %s is not in spk2gender file %s" % (speaker, spk2gender_file))
               ok = False
               if exit_on_first_error:
                   sys.exit(1)
                     
       #check that wavfile exists and is in right format (16kHz mono)
           wavfile = m.group(3)
           corpusdir = os.path.dirname(corpusfile)
           pathtowavfile = "%s/%s" % (corpusdir, wavfile)
           if not os.path.isfile(pathtowavfile):
               print("ERROR: wavfile %s doesn't exist" % (pathtowavfile,))
               ok = False
               if exit_on_first_error:
                   sys.exit(1)
           else:
               w = wave.open(pathtowavfile)
               channels = w.getnchannels()
               rate = w.getframerate()
               if channels != 1 or rate != 16000:
                   print("ERROR: wavfiles need to be 16kHz mono. %s is %d Hz, number of channels: %d" % (pathtowavfile,rate,channels))
                   ok = False
                   if exit_on_first_error:
                       sys.exit(1)

       #check that text and trans match
           text = m.group(4).split(" ")
           trans = m.group(5).split(" # ")
           if not len(text) == len(trans):
               print("ERROR: text and transcription are not equal length!\nText  (%d): %s\nTrans (%d): %s" % (len(text), text, len(trans), trans))
               ok = False
               if exit_on_first_error:
                   sys.exit(1)
               
   return ok
    

def writeLanguageFiles(expdir,corpusfiles):
    pass

def splitTrainTest(corpusfiles):
    return (None,None)

def writeDataFiles(expdir, traintest, data):
    pass






if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(usage)
        sys.exit(1)

    expdir = "%s/%s" % (kaldi_base,sys.argv[1])
    corpusfiles = sys.argv[2:]

    main(kaldi_base, expdir, corpusfiles)

    
