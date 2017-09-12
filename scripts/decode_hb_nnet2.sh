testfile=$1
graphdir=$2
modeldir=$3

echo "decode_test $testfile" > transcriptions/wav.scp
echo "decode_test test" > transcriptions/utt2spk
echo "decode_test <UNK>" > transcriptions/text

source ./path.sh



compute-mfcc-feats \
    --config=conf/mfcc.conf \
    scp:transcriptions/wav.scp \
    ark,scp:transcriptions/feats.ark,transcriptions/feats.scp

nnet-latgen-faster \
    --word-symbol-table=$graphdir/graph/words.txt \
    $modeldir/final.mdl \
    $graphdir/graph/HCLG.fst \
    ark:transcriptions/feats.ark \
    ark,t:transcriptions/lattices.ark;

lattice-best-path \
    --word-symbol-table=$graphdir/graph/words.txt \
    ark:transcriptions/lattices.ark \
    ark,t:transcriptions/one-best.tra;

utils/int2sym.pl -f 2- \
    $graphdir/graph/words.txt \
    transcriptions/one-best.tra \
    > transcriptions/one-best-hypothesis.txt;

cat transcriptions/one-best-hypothesis.txt
