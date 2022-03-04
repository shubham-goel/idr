ASIN=Schleich_Bald_Eagle
# PREPROCESS
python -m preprocess.preprocess_cameras --source_dir /home/shubham/data/GSO_for_idr/google/r30t0h0/v8/$ASIN/;
python -m preprocess.preprocess_cameras --source_dir /home/shubham/data/GSO_for_idr/google/r30t0h0/v8/$ASIN/ --use_linear_init;

# TRAIN
python training/exp_runner.py --train_cameras --conf ./confs/gso_trained_cameras_r30v8.conf --is_continue --scan_id $ASIN

# EXPORT
python evaluation/eval_export.py --conf ./confs/gso_trained_cameras_r30v8.conf --eval_cameras --resolution 256 --scan_id $ASIN
