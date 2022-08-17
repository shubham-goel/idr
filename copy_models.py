from pathlib2 import Path
import shutil

eval_directory = Path(__file__).parent / 'evals'
exp_directory = Path(__file__).parent / 'exps'
final_directory = Path(__file__).parent / 'final_models'
final_directory.mkdir(exist_ok=True)
setting = 'r0v20'

print('######### EVAL ############')
## Iterate over all folders in eval_directory
for folder in eval_directory.iterdir():
    break
    if folder.is_dir():
        # Check  if setting is correct
        if setting not in folder.name:
            continue

        # Find all .ply files in folder
        ply_files = [f for f in folder.iterdir() if f.suffix == '.ply']
        if len(ply_files) > 0:
            print('eval', folder.name)
            ply_file = ply_files[0]

            # Copy to final_directory
            shutil.copy(ply_file, final_directory / f'{folder.name}-idr-{ply_file.name}')

        # If eval extraction failed, use the last checkpointed exp as final model
        if (len(ply_files) == 0) or True:
            # Fetch latest ply file from exp dir instead
            exp_dir = exp_directory / folder.name

            ## subfolder with largest name
            subfolder = max(exp_dir.iterdir(), key=lambda x: x.name)
            exp_dir = subfolder / 'plots'
        
            # Find all .ply files in exp_dir
            ply_files = [f for f in exp_dir.iterdir() if f.suffix == '.ply']
        
            if len(ply_files) > 0:
                print('exp ', folder.name)
            else:
                breakpoint()

            # Find latest ply file (by name)
            ply_file = max(ply_files, key=lambda x: int(x.stem.split('_')[-1]))

        # Copy to final_directory
        shutil.copy(ply_file, final_directory / f'{folder.name}-idr-{ply_file.name}')

print('######### GT ############')
### Copy all gt models
gt_directory = Path(__file__).parent / 'gt_models'
gt_directory.mkdir(exist_ok=True)
GSO_directory = Path('/home/shubham/.ignition/fuel/fuel.ignitionrobotics.org/GoogleResearch/directdl/') # Em

## Iterate over all asins in 'code/all_benchmark_google_asins.txt'
all_asins = Path(__file__).parent / 'code' / 'all_benchmark_google_asins.txt'

# Read as list
with open(all_asins, 'r') as f:
    asins = [line.strip() for line in f]

for asin in asins:
    src = GSO_directory / asin / '1' / 'meshes' / 'model.obj'
    dst = gt_directory / f'{asin}-gt.obj'
    shutil.copy(src, dst)
