

#bash decode_hb_2.sh ~/alphabet_sr_test/O_anb_synth_16.wav exp/tri1/ 16
#?? bash decode_hb_2.sh ~/alphabet_sr_test/O_anb_synth_16.wav exp/nnet2/nnet2_simple/ 11


testfile=$1
graphdir=$2
modeldir=$2
tranumber=$3
#exp/tri1 16
#exp/nnet2 11

echo "decode_test $testfile" > transcriptions/wav.scp
echo "decode_test test" > transcriptions/utt2spk
echo "decode_test <UNK>" > transcriptions/text

source ./path.sh

steps/make_mfcc.sh --nj 1 --cmd "run.pl" transcriptions transcriptions/make_mfcc/test mfcc
steps/compute_cmvn_stats.sh transcriptions transcriptions/make_mfcc/test mfcc

utils/utt2spk_to_spk2utt.pl transcriptions/utt2spk > transcriptions/spk2utt
steps/decode.sh --config conf/decode.config --nj 1 --cmd "run.pl" $graphdir/graph transcriptions $modeldir/decode
utils/int2sym.pl -f 2- data/lang/words.txt $modeldir/decode/scoring/$tranumber.tra 
