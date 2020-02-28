#-*- coding: utf-8 -*-
import sys, os, io, re, wave, random

#Using corpusfiles to setup sphinx.

#input:
#experiment dir (<exp>)
#db name (<db>) should be same as <exp> really?
#spk2gender file (??)
#a list of corpusfiles 
#how to split into train|test


#Files for sphinx:
# ├─ etc
# │  ├─ your_db.dic                 (Phonetic dictionary)
# │  ├─ your_db.phone               (Phoneset file)
# │  ├─ your_db.lm.DMP              (Language model)
# │  ├─ your_db.filler              (List of fillers)
# │  ├─ your_db_train.fileids       (List of files for training)
# │  ├─ your_db_train.transcription (Transcription for training)
# │  ├─ your_db_test.fileids        (List of files for testing)
# │  └─ your_db_test.transcription  (Transcription for testing)
# └─ wav
#    ├─ speaker_1
#    │   └─ file_1.wav              (Recording of speech utterance)
#    └─ speaker_2
#       └─ file_2.wav

#output:
#<exp>/etc/<db>.txt (? use to create language model?)
#<exp>/etc/<db>.dic, <db>.phone, <db>.filler (silence etc)
#<exp>/etc/<db>.lm.DMP
#<exp>/etc/<db>_train.fileids, <db>_train.transcription
#<exp>/etc/<db>_test.fileids, <db>_test.transcription


#default settings for sphinxbase, split_method
#TODO allow setting these with command line options

sphinx_base = "/home/harald/sphinxtrain_test/"
split_method = "random_percentage" #random_percentage, random_number, corpusfile, speaker, list ..
test_percentage = 2
silence_phones = [("!SIL","sil"), ("<UNK>","spn")]

exit_on_first_error = True
exit_on_file_error = False

srilm_path = "/home/harald/git/kaldi/tools/srilm/bin/i686-m64/"

usage = "Usage: python makeSphinxFiles.py <experiment-directory> <corpusfile1> .. <corpusfileN>\nExample: python ../kaldi_stuff/makeSphinxFiles.py irish_named_entities_test *_named_entities/corpusfile.txt"

spk2gender_dict = {}
corpusdict = {}

def main(sphinx_base, expdir, corpusfiles):

    print("Exp dir: %s\nCorpusfiles: %s" % (expdir, corpusfiles))

    #check that sphinx_base exists and is writable
    if os.access(sphinx_base, os.W_OK):
        print("sphinx base %s is ok" % sphinx_base)
    else:
        if not os.path.isdir(sphinx_base):
            print("sphinx base %s doesn't exist" % sphinx_base)
        else:
            print("You don't have permission to write to sphinx base %s" % sphinx_base)


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

    #Split train/test
    traintestdicts = splitTrainTest()
    createSphinxData(traintestdicts)
    writeSphinxLanguageFiles(expdir)
    writeSphinxDataFiles(expdir,traintestdicts)

 
def validate_corpusfile(corpusfile):
    fh = io.open(corpusfile,"r",encoding="utf-8")
    lines = fh.readlines()
    linenr = 0
    ok = True
    for line in lines:
        line = line.strip()
        linenr += 1

        #definition of fields
        speaker_re = u"[a-z0-9]+"
        #Don't allow fileids that don't start with speaker name
        fileid_re = u"%s_[a-zA-Z0-9_-]+" % speaker_re
        #Allow fileids that don't start with speaker name
        #fileid_re = u".*%s_[a-zA-Z0-9_-]+" % speaker_re
        wavfile_re = u"[a-zA-Z0-9_/.-]+.wav"
        text_re = u"[a-záéíóú0-9 '|-]+"
        trans_re = u"[a-z@# _]+"
        
        #regexp = "^(%s)\t(%s)\t(%s)\t(%s)\t(%s)$" % (fileid_re,speaker_re,wavfile_re,text_re,trans_re)
        #m = re.match(regexp, line)
        #if not m:
        #    print(u"Error in %s line %d (doesn't match regexp \"%s\": %s" % (corpusfile, linenr, regexp, line))
        #    ok = False
       
        try:    
            (fileid,speaker,wavfile,text,trans) = line.split("\t")
        except:
            ok = False
            print("Error in line %s" % line)


        if not re.match(fileid_re,fileid):
            ok = False
            print("Error in fileid %s - regexp %s" % (fileid, fileid_re))
        if not re.match(speaker_re,speaker):
            ok = False
            print("Error in speaker %s - regexp %s" % (speaker, speaker_re))
        if not re.match(wavfile_re,wavfile):
            ok = False
            print("Error in wavfile %s - regexp %s" % (wavfile, wavfile_re))
        if not re.match(text_re,text):
            ok = False
            print("Error in text %s - regexp %s" % (text, text_re))
        if not re.match(trans_re,trans):
            ok = False
            print("Error in trans %s - regexp %s" % (trans, trans_re))

        if not ok and exit_on_first_error:
            sys.exit(1)
        else:
            #check that wavfile exists and is in right format (16kHz mono)
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
            text = text.split(" ")
            trans = trans.split(" # ")
            if not len(text) == len(trans):
                print("ERROR: text and transcription are not equal length!\nText  (%d): %s\nTrans (%d): %s" % (len(text), text, len(trans), trans))
                ok = False
                if exit_on_first_error:
                    sys.exit(1)
               
        if fileid in corpusdict:
            print("ERROR: fileid is duplicated:\n1: %s %s\n2:%s %s %s %s %s" % (fileid, corpusdict[fileid], fileid, speaker, wavfile, text, trans))
            ok = False
            if exit_on_first_error:
                sys.exit(1)
        else:
            path_to_wavfile = "%s/%s" % (os.path.dirname(os.path.abspath(corpusfile)), wavfile)
            corpusdict[fileid] = (speaker,path_to_wavfile,text,trans)
            #print("Adding to corpusdict: %s %s" % (fileid,corpusdict[fileid]))
    return ok
    

def splitTrainTest():
    traindict = {"mode": "train", "dict":{}, "spk2gender":{}}
    testdict = {"mode": "test", "dict": {}, "spk2gender":{}}
    if split_method == "random_percentage":
        for key in corpusdict:
            p = random.randint(0,100)
            #print("Selecting train/test for %s: %d > %d ?" % (key,p,test_percentage))
            if p > test_percentage:
                traindict["dict"][key] = corpusdict[key]
            else:
                testdict["dict"][key] = corpusdict[key]
    else:
        print("ERROR: split_method %s not implemented" % split_method)
        sys.exit(1)
            
    return [traindict,testdict]

sphinx_corpus = []
sphinx_lexicon = {}
sphinx_phones = {}
def createSphinxData(traintestdicts):
    for cdict in traintestdicts:
        mode = cdict["mode"]
        #print("Mode: %s" % mode)
        for fileid in cdict["dict"]:
            #print("Fileid: %s" % fileid)
            (speaker, wavfile, text, text_trans) = cdict["dict"][fileid]
            #Create language data
            sphinx_corpus.append(text)
            i = 0
            while i < len(text):
                word = text[i]
                trans = text_trans[i]
                # sphinx_lexicon = {word: {"count":count, "trans":{trans1:count,trans2:count, ..}}}
                if word in sphinx_lexicon:
                    sphinx_lexicon[word]["count"] += 1
                    sphinx_transcriptions = sphinx_lexicon[word]["trans"]
                    if trans in sphinx_transcriptions:
                        sphinx_transcriptions[trans] += 1
                    else:
                        sphinx_transcriptions[trans] = 1
                else:
                    sphinx_lexicon[word] = {"count":1, "trans":{trans: 1}}
                for phone in trans.split(" "):
                    if phone in sphinx_phones:
                        sphinx_phones[phone] += 1
                    else:
                        sphinx_phones[phone] = 1
                i += 1



def writeSphinxLanguageFiles(expdir,db_name):
    sphinx_lexicon_file="etc/%s.dict" % db_name
    sphinx_phones_file="etc/%s.phone" % db_name
    sphinx_fillers_file="etc/%s.fillers" % db_name


    if TRAIN_LANGUAGE_MODEL:
        sphinx_corpus_file="etc/%s.txt" % db_name
        sphinx_lm_file="etc/%s.lm" % db_name

        #corpus file (only necessary to build language model!)
        path_to_sphinx_corpus_file = "%s/%s" % (expdir,sphinx_corpus_file)
        if not os.path.exists(os.path.dirname(path_to_sphinx_corpus_file)):
            os.makedirs(os.path.dirname(path_to_sphinx_corpus_file))

        fh = io.open(path_to_sphinx_corpus_file,"w",encoding="utf-8")   
        sphinx_corpus.sort()
        for text in sphinx_corpus:
            fh.write(u"%s\n" % " ".join(text))
        fh.close()
        print("Written %d lines to %s" % (len(sphinx_corpus),path_to_sphinx_corpus_file))
        #Train language model
        train_lm_cmd = "%s/ngram_count -kndiscount -interpolate -text %s -lm %s" % (srilm_path, sphinx_corpus_file, sphinx_lm_file)
        print("Train lm command:\n%s" % train_lm_cmd)
        #os.system(train_lm_cmd)

        

    #lexicon file
    path_to_sphinx_lexicon_file = "%s/%s" % (expdir,sphinx_lexicon_file)
    if not os.path.exists(os.path.dirname(path_to_sphinx_lexicon_file)):
        os.makedirs(os.path.dirname(path_to_sphinx_lexicon_file))

    fh = io.open(path_to_sphinx_lexicon_file,"w",encoding="utf-8")  

    ##First write the silences to lexicon file
    ##Don't think this applies to sphinx
    #for (w,t) in silence_phones:
    #    fh.write(u"%s %s\n" % (w,t))

    ##Write each word to lexicon file
    counter = len(silence_phones)
    for word in sorted(sphinx_lexicon.keys()):
        for trans in sphinx_lexicon[word]["trans"]:
            fh.write(u"%s %s\n" % (word,trans))
            counter += 1
    fh.close()
    print("Written %d lines to %s" % (counter,path_to_sphinx_lexicon_file))

    #phones file
    path_to_sphinx_phones_file = "%s/%s" % (expdir,sphinx_phones_file)
    fh = io.open(path_to_sphinx_phones_file,"w",encoding="utf-8")  
    #print(sphinx_phones)
    for phone in sphinx_phones:
        fh.write(u"%s\n" % phone)
    fh.close()
    print("Written %d lines to %s" % (len(sphinx_phones),path_to_sphinx_phones_file))

    #fillers file
    path_to_sphinx_fillers_file = "%s/%s" % (expdir,sphinx_fillers_file)
    fh = io.open(path_to_sphinx_fillers_file,"w",encoding="utf-8")  

    for (w,t) in silence_phones:
        fh.write(u"%s\n" % t)
    fh.close()
    print("Written %d lines to %s" % (len(silence_phones),path_to_fillers_phones_file))


def writeSphinxDataFiles(expdir, traintestdicts):
    for cdict in traintestdicts:
        mode = cdict["mode"]
        traintestdir = re.sub(r"<traintest>", mode, sphinx_datadir)
        datadir = "%s/%s" % (expdir, traintestdir)

        if not os.path.exists(datadir):
            os.makedirs(datadir)

        #spk2gender
        path_to_sphinx_spk2gender_file = "%s/%s" % (datadir,sphinx_spk2gender_file)
        fh = io.open(path_to_sphinx_spk2gender_file,"w",encoding="utf-8")  
        for speaker in cdict["spk2gender"]:
            fh.write(u"%s %s\n" % (speaker, cdict["spk2gender"][speaker]))
        fh.close()
        print("Written %d lines to %s" % (len(cdict["spk2gender"]),path_to_sphinx_spk2gender_file))

        #utt2spk
        path_to_sphinx_utt2spk_file = "%s/%s" % (datadir,sphinx_utt2spk_file)
        fh = io.open(path_to_sphinx_utt2spk_file,"w",encoding="utf-8")  
        for fileid in sorted(cdict["dict"].keys()):
            (speaker,wavfile,text,trans) = cdict["dict"][fileid]
            fh.write(u"%s %s\n" % (fileid, speaker))
        fh.close()
        print("Written %d lines to %s" % (len(cdict["dict"]),path_to_sphinx_utt2spk_file))
                                             
        #wav.scp
        path_to_sphinx_wav_scp_file = "%s/%s" % (datadir,sphinx_wav_scp_file)
        fh = io.open(path_to_sphinx_wav_scp_file,"w",encoding="utf-8")  
        for fileid in sorted(cdict["dict"].keys()):
            (speaker,wavfile,text,trans) = cdict["dict"][fileid]
            fh.write(u"%s %s\n" % (fileid, wavfile))
        fh.close()
        print("Written %d lines to %s" % (len(cdict["dict"]),path_to_sphinx_wav_scp_file))

        #text
        path_to_sphinx_text_file = "%s/%s" % (datadir,sphinx_text_file)
        fh = io.open(path_to_sphinx_text_file,"w",encoding="utf-8")  
        for fileid in sorted(cdict["dict"].keys()):
            (speaker,wavfile,text,trans) = cdict["dict"][fileid]
            fh.write(u"%s %s\n" % (fileid, " ".join(text)))
        fh.close()
        print("Written %d lines to %s" % (len(cdict["dict"]),path_to_sphinx_text_file))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(usage)
        sys.exit(1)

    expdir = "%s/%s" % (db_base_dir,sys.argv[1])
    corpusfiles = sys.argv[2:]

    main(db_base_dir, expdir, corpusfiles)

    
