#-*- coding: utf-8 -*-
import sys, os, io, re, wave, random

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
spk2gender_file = "data/spk2gender"
split_method = "random_percentage" #random_percentage, random_number, corpusfile, speaker, list ..
test_percentage = 2
silence_phones = [("!SIL","sil"), ("<UNK>","spn")]

exit_on_first_error = True
exit_on_file_error = False

kaldi_corpus_file="data/local/corpus.txt"
kaldi_lexicon_file="data/local/dict/lexicon.txt"
kaldi_nonsilence_phones_file="data/local/dict/nonsilence_phones.txt"
kaldi_silence_phones_file="data/local/dict/silence_phones.txt"
kaldi_optional_silence_file="data/local/dict/optional_silence.txt"

kaldi_datadir = "data/<traintest>"
kaldi_spk2gender_file="spk2gender"
kaldi_wav_scp_file="wav.scp"
kaldi_text_file="text"
kaldi_utt2spk_file="utt2spk"

usage = "Usage: python makeKaldiFiles.py <experiment-directory> <corpusfile1> .. <corpusfileN>\nExample: python ../kaldi_stuff/makeKaldiFiles.py irish_named_entities_test *_named_entities/corpusfile.txt"

spk2gender_dict = {}
corpusdict = {}

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

    #Split train/test
    traintestdicts = splitTrainTest()
    #Write language files 
    #<exp>/data/local/corpus.txt
    #<exp>/data/local/dict/lexicon.txt, nonsilence_phones.txt, silence_phones.txt, optional_silence.txt
    #Write train/test files
    #<exp>/data/<train|test>/spk2gender, utt2spk, wav.scp, text
    createKaldiData(traintestdicts)
    writeKaldiLanguageFiles(expdir)
    writeKaldiDataFiles(expdir,traintestdicts)

def validate_spk2gender_file(spk2gender_file):
   fh = io.open(spk2gender_file,"r",encoding="utf-8")
   lines = fh.readlines()
   linenr = 0
   ok = True
   for line in lines:
       line = line.strip()
       linenr += 1
       regexp = "^([a-z0-9_]+)\t([mf])$"
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
        speaker_re = u"[a-z0-9]+"
        #Don't allow fileids that don't start with speaker name
        #fileid_re = u"%s_[a-zA-Z0-9_-]+" % speaker_re
        #Allow fileids that don't start with speaker name
        fileid_re = u".*%s_[a-zA-Z0-9_-]+" % speaker_re
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
            #fileid = m.group(1)
            #check that speaker is in spk2gender file
            #speaker = m.group(2)
            if speaker not in spk2gender_dict:
                print("ERROR: speaker %s is not in spk2gender file %s" % (speaker, spk2gender_file))
                ok = False
                if exit_on_first_error:
                    sys.exit(1)
                     
            #check that wavfile exists and is in right format (16kHz mono)
            #wavfile = m.group(3)
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
            #text = m.group(4).split(" ")
            #trans = m.group(5).split(" # ")
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

kaldi_corpus = []
kaldi_lexicon = {}
kaldi_phones = {}
def createKaldiData(traintestdicts):
    for cdict in traintestdicts:
        mode = cdict["mode"]
        #print("Mode: %s" % mode)
        for fileid in cdict["dict"]:
            #print("Fileid: %s" % fileid)
            (speaker, wavfile, text, text_trans) = cdict["dict"][fileid]
            #Create language data
            kaldi_corpus.append(text)
            i = 0
            while i < len(text):
                word = text[i]
                trans = text_trans[i]
                # kaldi_lexicon = {word: {"count":count, "trans":{trans1:count,trans2:count, ..}}}
                if word in kaldi_lexicon:
                    kaldi_lexicon[word]["count"] += 1
                    kaldi_transcriptions = kaldi_lexicon[word]["trans"]
                    if trans in kaldi_transcriptions:
                        kaldi_transcriptions[trans] += 1
                    else:
                        kaldi_transcriptions[trans] = 1
                else:
                    kaldi_lexicon[word] = {"count":1, "trans":{trans: 1}}
                for phone in trans.split(" "):
                    if phone in kaldi_phones:
                        kaldi_phones[phone] += 1
                    else:
                        kaldi_phones[phone] = 1
                i += 1

            #create train/test data
            if speaker not in cdict["spk2gender"]:
                #print("adding to %s data spk2gender: %s %s" % (mode, speaker, spk2gender_dict[speaker]))
                cdict["spk2gender"][speaker] = spk2gender_dict[speaker]


def writeKaldiLanguageFiles(expdir):
    #corpus.txt
    path_to_kaldi_corpus_file = "%s/%s" % (expdir,kaldi_corpus_file)
    if not os.path.exists(os.path.dirname(path_to_kaldi_corpus_file)):
        os.makedirs(os.path.dirname(path_to_kaldi_corpus_file))

    fh = io.open(path_to_kaldi_corpus_file,"w",encoding="utf-8")   
    kaldi_corpus.sort()
    for text in kaldi_corpus:
        fh.write(u"%s\n" % " ".join(text))
    fh.close()
    print("Written %d lines to %s" % (len(kaldi_corpus),path_to_kaldi_corpus_file))

    #lexicon.txt
    path_to_kaldi_lexicon_file = "%s/%s" % (expdir,kaldi_lexicon_file)
    if not os.path.exists(os.path.dirname(path_to_kaldi_lexicon_file)):
        os.makedirs(os.path.dirname(path_to_kaldi_lexicon_file))

    fh = io.open(path_to_kaldi_lexicon_file,"w",encoding="utf-8")  

    ##First write the silences to lexicon file
    for (w,t) in silence_phones:
        fh.write(u"%s %s\n" % (w,t))

    ##Then write each word to lexicon file
    counter = len(silence_phones)
    for word in sorted(kaldi_lexicon.keys()):
        for trans in kaldi_lexicon[word]["trans"]:
            fh.write(u"%s %s\n" % (word,trans))
            counter += 1
    fh.close()
    print("Written %d lines to %s" % (counter,path_to_kaldi_lexicon_file))

    #nonsilence_phones.txt
    path_to_kaldi_nonsilence_phones_file = "%s/%s" % (expdir,kaldi_nonsilence_phones_file)
    fh = io.open(path_to_kaldi_nonsilence_phones_file,"w",encoding="utf-8")  
    #print(kaldi_phones)
    for phone in kaldi_phones:
        fh.write(u"%s\n" % phone)
    fh.close()
    print("Written %d lines to %s" % (len(kaldi_phones),path_to_kaldi_nonsilence_phones_file))
    #silence_phones.txt
    path_to_kaldi_silence_phones_file = "%s/%s" % (expdir,kaldi_silence_phones_file)
    fh = io.open(path_to_kaldi_silence_phones_file,"w",encoding="utf-8")  

    for (w,t) in silence_phones:
        fh.write(u"%s\n" % t)
    fh.close()
    print("Written %d lines to %s" % (len(silence_phones),path_to_kaldi_silence_phones_file))

    #optional_silence.txt
    path_to_kaldi_optional_silence_file = "%s/%s" % (expdir,kaldi_optional_silence_file)
    fh = io.open(path_to_kaldi_optional_silence_file,"w",encoding="utf-8")  

    (w,t) = silence_phones[0]
    fh.write(u"%s\n" % t)
    fh.close()
    print("Written %d line to %s" % (1,path_to_kaldi_optional_silence_file))

def writeKaldiDataFiles(expdir, traintestdicts):
    for cdict in traintestdicts:
        mode = cdict["mode"]
        traintestdir = re.sub(r"<traintest>", mode, kaldi_datadir)
        datadir = "%s/%s" % (expdir, traintestdir)

        if not os.path.exists(datadir):
            os.makedirs(datadir)

        #spk2gender
        path_to_kaldi_spk2gender_file = "%s/%s" % (datadir,kaldi_spk2gender_file)
        fh = io.open(path_to_kaldi_spk2gender_file,"w",encoding="utf-8")  
        for speaker in cdict["spk2gender"]:
            fh.write(u"%s %s\n" % (speaker, cdict["spk2gender"][speaker]))
        fh.close()
        print("Written %d lines to %s" % (len(cdict["spk2gender"]),path_to_kaldi_spk2gender_file))

        #utt2spk
        path_to_kaldi_utt2spk_file = "%s/%s" % (datadir,kaldi_utt2spk_file)
        fh = io.open(path_to_kaldi_utt2spk_file,"w",encoding="utf-8")  
        for fileid in sorted(cdict["dict"].keys()):
            (speaker,wavfile,text,trans) = cdict["dict"][fileid]
            fh.write(u"%s %s\n" % (fileid, speaker))
        fh.close()
        print("Written %d lines to %s" % (len(cdict["dict"]),path_to_kaldi_utt2spk_file))
                                             
        #wav.scp
        path_to_kaldi_wav_scp_file = "%s/%s" % (datadir,kaldi_wav_scp_file)
        fh = io.open(path_to_kaldi_wav_scp_file,"w",encoding="utf-8")  
        for fileid in sorted(cdict["dict"].keys()):
            (speaker,wavfile,text,trans) = cdict["dict"][fileid]
            fh.write(u"%s %s\n" % (fileid, wavfile))
        fh.close()
        print("Written %d lines to %s" % (len(cdict["dict"]),path_to_kaldi_wav_scp_file))

        #text
        path_to_kaldi_text_file = "%s/%s" % (datadir,kaldi_text_file)
        fh = io.open(path_to_kaldi_text_file,"w",encoding="utf-8")  
        for fileid in sorted(cdict["dict"].keys()):
            (speaker,wavfile,text,trans) = cdict["dict"][fileid]
            fh.write(u"%s %s\n" % (fileid, " ".join(text)))
        fh.close()
        print("Written %d lines to %s" % (len(cdict["dict"]),path_to_kaldi_text_file))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(usage)
        sys.exit(1)

    expdir = "%s/%s" % (kaldi_base,sys.argv[1])
    corpusfiles = sys.argv[2:]

    main(kaldi_base, expdir, corpusfiles)

    
