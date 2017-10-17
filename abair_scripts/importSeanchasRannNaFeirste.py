import os, re, glob, io


#script to import the seanchas rann na feirste files.
#needs some special things because the speakers are mixed
#so
#1) list speakers
#2) for each speaker mkdir data|audio/<speaker>_seanchas_rann_na_feirste 
#3) make README.txt and import.sh
#4) copy wavfiles (same call as in import.sh)
#5) make corpusfile (same call as in import.sh)

svndir = "/var/phonetics/svn/Corpora/ga_UL/seanchas_rann_na_feirste/corpus"
datadir = "data"
audiodir = "audio"
basename = "_seanchas_rann_na_feirste"

txtfiles = glob.glob("%s/txt/*.txt" % svndir)
txtfiles.sort()

speakers = {}
for txtfile in txtfiles:
    m = re.search(r"_([a-z]+)_[0-9]+.txt", txtfile)
    speaker = m.group(1)
    if speaker in speakers:
        speakers[speaker] += 1
    else:
        speakers[speaker] = 1

for speaker in speakers:
    print("Making files for speaker: %s" % speaker)
    speakerdir = "%s%s" % (speaker, basename)
    speakerdatadir = "%s/%s" % (datadir,speakerdir)
    speakeraudiodir = "%s/%s" % (audiodir,speakerdir)

    readmefile = "%s/README.txt" % speakerdatadir
    importfile = "%s/import.sh" % speakerdatadir


    readmetxt = u"""
Recordings from Seanchas Rann na Feirste.

speaker: %s
gender: %s

wav files: %s
txt files: %s

import script: import.sh
""" % (speaker, speaker[-1], "%s/wav/*%s_[0-9]+.wav" % (svndir,speaker), "%s/txt/*%s_[0-9]+.txt" % (svndir, speaker))

    importtxt = u"""
#mkdir -p ../../%s/wav
#cp %s ../../%s/wav

python ../../scripts/abair_scripts/convertTxtToCorpusfile.py . ../../%s/wav %s
""" % (speakeraudiodir,"%s/wav/*_%s_[0-9]*.wav" % (svndir,speaker), speakeraudiodir, speakeraudiodir, "%s/txt/*_%s_[0-9]*.txt" % (svndir, speaker))

    #print(readmetxt)
    #print(importtxt)

    if not os.path.exists(speakerdatadir):
        print("Making directory %s" % speakerdatadir)
        os.makedirs(speakerdatadir)
    else:
        print("Directory %s exists" % speakerdatadir)

    print("Writing file %s" % readmefile)
    rfh = io.open(readmefile,"w",encoding="utf-8")
    rfh.write(readmetxt)
    rfh.close()

    print("Writing file %s" % importfile)
    ifh = io.open(importfile,"w",encoding="utf-8")
    ifh.write(importtxt)
    ifh.close()

    owd = os.getcwd()
    os.chdir(speakerdatadir)
    os.system("rm corpusfile.txt; sh import.sh")
    os.chdir(owd)
    #sys.exit()
