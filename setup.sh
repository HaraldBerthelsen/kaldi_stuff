#name=irish_new_test
#audio=/home/harald/git/kaldi/egs/irish_alphabet/audio

#name=irish_named_entities_test
#audio=/home/harald/named_entities_3_dialects/

#name=irish_test_26oct
#corpusfiles=data/dodm_seanchas_rann_na_feirste/corpusfile.txt
#corpusfiles=data/*_named_entities/corpusfile.txt

#name=irish_test_26oct_all_data
#corpusfiles=data/dodm_seanchas_rann_na_feirste/corpusfile.txt
#corpusfiles=data/*/corpusfile.txt

name=irish_test_feb27_2020
corpusfiles=/home/harald/git/abair-gitea/abair-corpora/mileglor-macbook-air/*/corpusfile.txt


rm -rf /home/harald/git/kaldi/egs/$name

#Assumes $audio/(train|test)/<speaker>/<wav|xml>/<files>
#bash setup_data.sh $name $audio
#Assumes $audio/(train|test)/<speaker>/xml/<xmlfiles>
#bash setup_language_files.sh $name $audio

#Assumes corpusfiles!
#python scripts/makeKaldiFiles.py $name $corpusfiles
python makeKaldiFiles.py $name $corpusfiles

#cp -r scripts/scripts/* /home/harald/git/kaldi/egs/$name/
#cp -r scripts/conf /home/harald/git/kaldi/egs/$name/
cp -r scripts/* /home/harald/git/kaldi/egs/$name/
cp -r conf /home/harald/git/kaldi/egs/$name/

cd /home/harald/git/kaldi/egs/$name/


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


# if ! bash run.sh; then
#    exit 1
# fi

# if ! bash nnet2_simple/run_nnet2_simple.sh; then
#    exit 1
# fi


