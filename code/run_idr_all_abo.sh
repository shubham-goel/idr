#!/bin/bash
## SLURM scripts have a specific format.

### Section1: SBATCH directives to specify job configuration
## job name
#SBATCH --job-name=render
## filename for job standard output (stdout)
## %j is the job id, %u is the user id, %A is $SLURM_ARRAY_JOB_ID, %a is $SLURM_ARRAY_TASK_ID
#SBATCH --output=/home/%u/checkpoint/jobs/idr-abo-%A_%a.out
#SBATCH --error=/home/%u/checkpoint/jobs/idr-abo-%A_%a.err

##SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=5
#SBATCH --time=10:00:00
#SBATCH --qos=low
##SBATCH --nodelist=em1,em2,em4,em8,em9
#SBATCH --exclude=em3
#SBATCH --array=0-7
#SBATCH --comment="IDR on ABO"
#SBATCH --signal=B:CONT@60                  #Signal is sent to batch script itself

### Section 2: Setting environment variables for the job
### Remember that all the module command does is set environment
### variables for the software you need to. Here I am assuming I
### going to run something with python.
### You can also set additional environment variables here and
### SLURM will capture all of them for each task
# !!!!!!!!!!!!!USE ENV WHEN CALLING SBATCH!!!!!!!!!!!


### Signal Handling
trap_handler () {
   echo "Caught signal: " $1
   # SIGTERM must be bypassed
   if [ "$1" = "TERM" ]; then
       echo "bypass sigterm"
   else
     # Submit a new job to the queue
     echo "Requeuing " $SLURM_ARRAY_JOB_ID $SLURM_ARRAY_TASK_ID
     # SLURM_JOB_ID is a unique representation of the job, equivalent
     # to above
     scontrol requeue $SLURM_JOB_ID
   fi
}

# Install signal handler
trap 'trap_handler USR1' USR1
trap 'trap_handler CONT' CONT
trap 'trap_handler TERM' TERM


### Section 3:
### Run your job.

# Rendering all (set --array=0-16):
# PREFIXES=("[0-9a-z].*" "[A].*" "[B].*" "[C].*" "[D].*" "[E].*" "[F].*" "[GHI].*" "[JKL].*" "[M].*" "[N].*" "[O].*" "[PQ].*" "[R].*" "[S].*" "[T].*" "[U-Z].*" )

# # Rendering all parallelly (set --array=0-1075%256 --partition=scavenge):
# # Uses all_google_asins.txt set using `ls /GoogleResearch/directdl/*.zip | sed -E 's#^/private/home/shubhamgoel/.ignition/fuel/fuel.ignitionrobotics.org/GoogleResearch/directdl/(.*).zip$#\1#' > all_google_asins.txt
# IFS=$'\r\n' GLOBIGNORE='*' command eval  'PREFIXES=($(cat all_google_asins.txt))'

# List of asins to run on (set --array=0-7):
# IFS=$'\r\n' GLOBIGNORE='*' command eval  'PREFIXES=($(cat all_benchmark_google_asins.txt))'
PREFIXES=("B07GQ3HVW1" "B07P23Y7XZ" "B079XDX31X" "B016CKGSZW" "B07DJPC8JB" "B001LTZZSG" "B01N2JGIPW" "B00GMGHCVG")

# PREPROCESS
python -m preprocess.preprocess_cameras --source_dir /home/shubham/data/GSO_for_idr/amazon/r0t0h0/v15/${PREFIXES[$SLURM_ARRAY_TASK_ID]}/;
python -m preprocess.preprocess_cameras --source_dir /home/shubham/data/GSO_for_idr/amazon/r0t0h0/v15/${PREFIXES[$SLURM_ARRAY_TASK_ID]}/ --use_linear_init;

# TRAIN
python training/exp_runner.py --train_cameras --conf ./confs/abo_trained_cameras_r0v15.conf --is_continue --scan_id ${PREFIXES[$SLURM_ARRAY_TASK_ID]}

# EVAL
# python evaluation/eval.py --conf ./confs/abo_trained_cameras_r0v15.conf --scan_id ${PREFIXES[$SLURM_ARRAY_TASK_ID]}
python evaluation/eval_export.py --conf ./confs/abo_trained_cameras_r0v15.conf --eval_cameras --resolution 256 --scan_id ${PREFIXES[$SLURM_ARRAY_TASK_ID]}
