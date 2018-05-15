#To train with mozilla deepspeech:

#csv file:
#cat data/ldc93s1/ldc93s1.csv 
#wav_filename,wav_filesize,transcript
#/home/harald/git/DeepSpeech/data/ldc93s1/LDC93S1.wav,93638,she had your dark suit in greasy wash water all year

#wav file:
#soxi data/ldc93s1/LDC93S1.wav 

#Input File     : 'data/ldc93s1/LDC93S1.wav'
#Channels       : 1
#Sample Rate    : 16000
#Precision      : 16-bit
#Duration       : 00:00:02.92 = 46797 samples ~ 219.361 CDDA sectors
#File Size      : 93.6k
#Bit Rate       : 256k
#Sample Encoding: 16-bit Signed Integer PCM

#ls -l data/ldc93s1/LDC93S1.wav 
#-rw-rw-r-- 1 harald harald 93638 Dec  1 19:14 data/ldc93s1/LDC93S1.wav

#txt file:
#cat data/ldc93s1/LDC93S1.txt 
#0 46797 She had your dark suit in greasy wash water all year.

#so

#csv file contains absolute path to wav file, size of wav file, and text downcased and without punctuation marks, comma-separated
#txt file contains start sample (0), end sample (46797), and text, space-separated
#wav file is 16 kHz mono

#In our corpusfile.txt we have
#nnc_CI0001CDNamedEntities01_0001	nnc	../../audio/nnc_named_entities/wav/CI0001CDNamedEntities01_0001.wav	na laethanta

#id, speaker, rel path to wav file, text

