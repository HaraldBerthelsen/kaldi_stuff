
#Read xml files, print lexicon.txt, nonsilence_phones.txt, silence_phones.txt and optional_silence.txt

#name=irish_new_test
name=$1

kaldiroot=/home/harald/git/kaldi
#xmldir=/home/harald/git/kaldi/egs/irish_alphabet/audio
xmldir=$2

cd $kaldiroot/egs
mkdir -p $name/data/local/dict
lexicon_file=$name/data/local/dict/lexicon.txt
nonsilence_phones_file=$name/data/local/dict/nonsilence_phones.txt
silence_phones_file=$name/data/local/dict/silence_phones.txt
optional_silence_file=$name/data/local/dict/optional_silence.txt

tmpdir=/tmp/kaldi_lang
rm -r $tmpdir
mkdir -p $tmpdir

#assume $xmldir/(train|test)/<speaker>/xml/<xmlfiles>

for xmldir in `find $xmldir/*/*/xml -type d`
do
    python /home/harald/svn/Software/Abair/scripts/convertFiles.py lex $tmpdir $xmldir/*.xml 2> /dev/null
done
cat $tmpdir/*.lex | sort -u > $tmpdir/tmp.lex

#fixes for the alphabet files
cat $tmpdir/tmp.lex | grep -v "SILENCE_TOKEN" | grep -v "None" | sed 's/xletter//g' | sed 's/ 0 / /g' > $tmpdir/tmp2.lex
mv $tmpdir/tmp2.lex $tmpdir/tmp.lex

echo "!SIL sil
<UNK> spn" > $lexicon_file
cat $tmpdir/tmp.lex >> $lexicon_file

cut -f 2- -d " " $tmpdir/tmp.lex | sed 's/ /\n/g' | sort -u | grep -v "^$" | grep -v "sil" > $nonsilence_phones_file

echo "sil
spn" > $silence_phones_file
echo "sil" > $optional_silence_file
