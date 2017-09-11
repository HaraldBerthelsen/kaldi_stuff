name=irish_new_test
audio=/home/harald/git/kaldi/egs/irish_alphabet/audio

rm -rf ../kaldi/egs/$name

#Assumes $audio/(train|test)/<speaker>/<wavfiles+txtfiles>
bash setup_data.sh $name $audio
#Assumes $audio/(train|test)/<speaker>/xml/<xmlfiles>
bash setup_language_files.sh $name $audio
cp -r scripts/* ../kaldi/egs/$name/
cp -r conf ../kaldi/egs/$name/

cd ../kaldi/egs/$name/

ln -s ../wsj/s5/utils
ln -s ../wsj/s5/steps
mkdir local
cp ../voxforge/s5/local/score.sh local/

bash utils/fix_data_dir.sh data/train
bash utils/fix_data_dir.sh data/test

if ! bash utils/validate_data_dir.sh --no-feats data/train; then
    exit 1
fi
    
if ! bash utils/validate_data_dir.sh --no-feats data/test; then
    exit 1
fi


if ! bash run.sh; then
   exit 1
fi

if ! bash nnet2_simple/run_nnet2_simple.sh; then
   exit 1
fi


