#For each corpusfile in data/*:
#Check that audiofile exists in audio/*
#check that audiofile has right format
#measure length of audiofile
#count nr of words and segments
#print speaker, gender, dialect, age?, length of recordings, nr words, nr segments
#print totals

import sys, os, logging, io, wave
from datetime import timedelta, datetime

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

print_all = False
#print_speaker = False
#print_total = False
#print_all = True
print_speaker = True
print_total = True

#Exit immediately on first error
exit_on_error = False


datadir_base = "data"
audiodir_base = "audio"


def validateDirectory(dirname):
    datadir = "%s/%s" % (datadir_base, dirname)
    logger.info("Dirname: %s" % dirname)
    
    #small test:
    #if dirname not in ["anb_named_entities"]:
    #    continue

    #check audio dir
    audiodir = "%s/%s/wav" % (audiodir_base, dirname)
    if not os.path.isdir(audiodir):
        msg = "Audio dir %s does not exist" % audiodir
        logger.error(msg)
        raise Exception(msg)

    corpusfile = "%s/corpusfile.txt" % datadir
    if not os.path.isfile(corpusfile):
        msg = "Corpusfile %s does not exist" % corpusfile
        logger.error(msg)
        raise Exception(msg)

    logger.info("Corpusfile: %s" % corpusfile)
    corpusfile_fh = io.open(corpusfile,"r",encoding="utf-8")
    corpusfile_lines = corpusfile_fh.readlines()
    corpusfile_fh.close()
    for corpusfile_line in corpusfile_lines:
        (fileid, speaker, wavfile, text, transcription) = corpusfile_line.strip().split("\t")
        #fileid format check?
        #check speaker is in spk2gender
        if not speaker in spk2gender:
            msg = "Speaker %s not in %s" % (speaker, spk2gender_file)
            logger.error(msg)
            raise Exception(msg)
            
        gender = spk2gender[speaker]

        #TODO use speaker database with more than gender!
        dialect = "u"
        age = "u"
        #check wavfile exists
        relative_wavfile = "%s/%s" % (datadir, wavfile)
        if not os.path.isfile(relative_wavfile):
            msg = "Wav file %s does not exist" % relative_wavfile
            logger.error(msg)
            raise Exception(msg)
        #check wavfile is right format
        wav = wave.open(relative_wavfile, 'rb')
        channels = wav.getnchannels()
        rate = wav.getframerate()
        if channels != 1 or rate != 16000:
            msg = "Wrong format of %s! channels: %d, rate: %d" % (relative_wavfile, channels, rate)
            logger.error(msg)
            raise Exception(msg)
        #get length of wavfile
        wav_length = wav.getnframes()/(rate*1.0)
        #logger.info("Wav %s length: %.2f s" % (relative_wavfile, wav_length))
        wav.close()
        #sys.exit()
        #check equal length of text and transcription
        text_list = text.split(" ")
        transcription_list = transcription.split(" # ")
        if not len(text_list) == len(transcription_list):
            msg = "Text and transcription not equal length!Text: %d, trans: %s\nText:  %s\nTrans: %s" % (len(text_list), len(transcription_list), text, transcription)
            logger.error(msg)
            raise Exception

        #check text format?
        #check transcription format?
        #get nr of words, nr of segments
        nwords = len(text_list)
        nsegments = 0
        for t in transcription_list:
            nsegments += len(t.split(" "))
        #save statistics
        stats[fileid] = (fileid, speaker, gender, dialect, age, wav_length, nwords, nsegments)



def convertTime(s):
    h = 0
    m = 0
    if s > 59:
        (m, s) = divmod(s,60)
    if m > 59:
        (h, m) = divmod(m,60)
    return (h,m,s)






spk2gender_file = "%s/spk2gender" % datadir_base
spk2gender_fh = io.open(spk2gender_file,"r",encoding="utf-8")
spk2gender = {}
for line in spk2gender_fh.readlines():
    (spk,gender) = line.strip().split("\t")
    spk2gender[spk] = gender
spk2gender_fh.close()




stats = {}

datadirs = os.walk(datadir_base).next()[1]
datadirs.sort()
for dirname in datadirs:
    try:
        validateDirectory(dirname)
    except Exception as e:
        if exit_on_error:
            print(e)
            sys.exit(1)
            

total_by_speaker = {}
total = [0,0,0]


for fileid in sorted(stats.keys()):
    #print("%s\t%s\t%s\t%s\t%s\t%.2f\t%d\t%d" % (fileid, speaker, gender, dialect, age, wav_length, nwords, nsegments))
    if print_all:
        print("%s\t%s\t%s\t%s\t%s\t%.2f\t%d\t%d" % stats[fileid])
    speaker = stats[fileid][1]
    if speaker not in total_by_speaker:
        total_by_speaker[speaker] = [0,0,0]
    
    total_by_speaker[speaker][0] += stats[fileid][5]
    total_by_speaker[speaker][1] += stats[fileid][6]
    total_by_speaker[speaker][2] += stats[fileid][7]
        
    total[0] += stats[fileid][5]
    total[1] += stats[fileid][6]
    total[2] += stats[fileid][7]
    
for speaker in sorted(total_by_speaker.keys()):
    wav_length = total_by_speaker[speaker][0]
    nwords = total_by_speaker[speaker][1]
    nsegments = total_by_speaker[speaker][2]
    (h, m, s) = convertTime(wav_length)
    if print_speaker:
        print("%s\t%10.2f\t(%d h, %d min, %d s)\t%d\t%d" % (speaker, wav_length, h, m, s, nwords, nsegments))

wav_length = total[0]
nwords = total[1]
nsegments = total[2]
(h, m, s) = convertTime(wav_length)
if print_total:
    print("TOTAL:\t%10.2f\t(%d h, %d min, %d s)\t%d\t%d" % (wav_length, h, m, s, nwords, nsegments))
