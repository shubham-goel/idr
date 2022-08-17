for asin in `cat  all_benchmark_google_asins.txt`; do
    echo $asin;
    # python -m preprocess.preprocess_cameras --source_dir /home/shubham/data/GSO_for_idr/google/r20t0h0/v8/$asin/;
    # python -m preprocess.preprocess_cameras --source_dir /home/shubham/data/GSO_for_idr/google/r20t0h0/v8/$asin/ --use_linear_init;
    python -m preprocess.preprocess_cameras --source_dir /home/shubham/data/GSO_for_idr/google/r30t0h0/v8/$asin/;
    python -m preprocess.preprocess_cameras --source_dir /home/shubham/data/GSO_for_idr/google/r30t0h0/v8/$asin/ --use_linear_init;
done
