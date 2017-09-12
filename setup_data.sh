
#name=irish_new_test
name=$1

kaldiroot=/home/harald/git/kaldi
#audio=/home/harald/git/kaldi/egs/irish_alphabet/audio
audio=$2

cd $kaldiroot/egs
mkdir -p $name
mkdir -p $name/data
mkdir -p $name/data/train
mkdir -p $name/data/test
mkdir -p $name/data/local

corpus_file=$name/data/local/corpus.txt
#rm $corpus_file

#assume $audio/(train|test)/<speaker>/<wavfiles>
for traintestdir in `find $audio/{train,test} -mindepth 0 -maxdepth 0 -type d`
do
    traintest=`basename "$traintestdir"`
    spk2gender_file=$name/data/$traintest/spk2gender
    wav_scp_file=$name/data/$traintest/wav.scp
    text_file=$name/data/$traintest/text
    utt2spk_file=$name/data/$traintest/utt2spk




    if [ -e $spk2gender_file ];then
        rm $spk2gender_file
        rm $wav_scp_file
        rm $text_file
        rm $utt2spk_file
    fi
    for speakerdir in `find $traintestdir -mindepth 1 -maxdepth 1 -type d`
    do
        speaker=`basename "$speakerdir"`
        echo $speakerdir
        echo $speaker

        case $speaker in
            nnc)
                gender=f;;
            pmc)
                gender=m;;
            anb)
                gender=f;;
            *)
                echo "Gender undefined for speaker $speaker, edit $spk2gender_file!"
                gender=undefined;;        
        esac
        echo "$speaker $gender" >> $spk2gender_file

        for wavfile in `find $speakerdir/wav/*.wav`
        do
            #wavfiledir=`dirname "$wavfile"`
            wavfilebase=`basename "$wavfile" .wav`
            utterance_id="${speaker}_${wavfilebase}"
            echo "$utterance_id $wavfile" >> $wav_scp_file
            echo "$utterance_id $speaker" >> $utt2spk_file

            #Get text from xml files, to make sure that everything matches
            xmlfile=$speakerdir/xml/$wavfilebase.xml
            txtdir=$speakerdir/txt
            txtfile=$txtdir/$wavfilebase.txt
            python ~/svn/Software/Abair/scripts/convertFiles.py txt $txtdir $xmlfile 2> /dev/null
            text=`cat $txtfile`
            #${,,} to downcase - does it work with utf-8? Seems like it..
            echo "$utterance_id ${text,,}" >> $text_file
            echo "${text,,}" >> $corpus_file
        done
    done
done
sort -u $corpus_file -o $corpus_file



