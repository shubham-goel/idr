## Exports final cameras and mesh to file. Used for DS CVPR2022 evaluation

import sys
sys.path.append('../code')
import argparse
import GPUtil
import os
from pyhocon import ConfigFactory
import torch
import numpy as np
import cvxpy as cp
from PIL import Image
import math

import utils.general as utils
import utils.plots as plt
from utils import rend_util

def evaluate(**kwargs):
    torch.set_default_dtype(torch.float32)

    conf = ConfigFactory.parse_file(kwargs['conf'])
    exps_folder_name = kwargs['exps_folder_name']
    evals_folder_name = kwargs['evals_folder_name']
    eval_cameras = kwargs['eval_cameras']

    expname = conf.get_string('train.expname') + kwargs['expname']
    scan_id = kwargs['scan_id'] if kwargs['scan_id'] != '-1' else conf.get_string('dataset.scan_id', default='-1')
    if scan_id != '-1':
        expname = expname + '_{0}'.format(scan_id)

    if kwargs['timestamp'] == 'latest':
        if os.path.exists(os.path.join('../', kwargs['exps_folder_name'], expname)):
            timestamps = os.listdir(os.path.join('../', kwargs['exps_folder_name'], expname))
            if (len(timestamps)) == 0:
                print('WRONG EXP FOLDER')
                exit()
            else:
                timestamp = sorted(timestamps)[-1]
        else:
            print('WRONG EXP FOLDER')
            exit()
    else:
        timestamp = kwargs['timestamp']

    utils.mkdir_ifnotexists(os.path.join('../', evals_folder_name))
    expdir = os.path.join('../', exps_folder_name, expname)
    evaldir = os.path.join('../', evals_folder_name, expname)
    utils.mkdir_ifnotexists(evaldir)

    model = utils.get_class(conf.get_string('train.model_class'))(conf=conf.get_config('model'))
    if torch.cuda.is_available():
        model.cuda()

    dataset_conf = conf.get_config('dataset')
    if kwargs['scan_id'] != '-1':
        dataset_conf['scan_id'] = kwargs['scan_id']
    eval_dataset = utils.get_class(conf.get_string('train.dataset_class'))(eval_cameras, **dataset_conf)

    # settings for camera optimization
    scale_mat = eval_dataset.get_scale_mat()
    if eval_cameras:
        num_images = len(eval_dataset)
        pose_vecs = torch.nn.Embedding(num_images, 7, sparse=True).cuda()
        pose_vecs.weight.data.copy_(eval_dataset.get_pose_init())

        gt_pose = eval_dataset.get_gt_pose()

    old_checkpnts_dir = os.path.join(expdir, timestamp, 'checkpoints')

    saved_model_state = torch.load(os.path.join(old_checkpnts_dir, 'ModelParameters', str(kwargs['checkpoint']) + ".pth"))
    model.load_state_dict(saved_model_state["model_state_dict"])
    epoch = saved_model_state['epoch']

    if eval_cameras:
        data = torch.load(os.path.join(old_checkpnts_dir, 'CamParameters', str(kwargs['checkpoint']) + ".pth"))
        pose_vecs.load_state_dict(data["pose_vecs_state_dict"])

    ####################################################################################################################
    print("evaluating...")

    model.eval()
    if eval_cameras:
        pose_vecs.eval()

    with torch.no_grad():
        if eval_cameras:
            gt_Rs = gt_pose[:, :3, :3].double()
            gt_ts = gt_pose[:, :3, 3].double()

            pred_Rs = rend_util.quat_to_rot(pose_vecs.weight.data[:, :4]).cpu().double()
            pred_ts = pose_vecs.weight.data[:, 4:].cpu().double()

        mesh = plt.get_surface_high_res_mesh(
            sdf=lambda x: model.implicit_network(x)[:, 0],
            resolution=kwargs['resolution']
        )

        # Export mesh, predicted cameras, gt cameras 
        mesh.export('{0}/surface_untransformed_unclean_{1}.obj'.format(evaldir, epoch), 'obj')
        # breakpoint()
        if eval_cameras:
            # Fetch intrinsics in screen space
            intrinsics = torch.stack(eval_dataset.intrinsics_all, dim=0)[:,:3,:3]

            gt_camera_poses = {
                'R': gt_Rs,
                't': gt_ts,
                'K': intrinsics,
            }

            pred_camera_poses = {
                'R': pred_Rs,
                't': pred_ts,
                'K': intrinsics,
                'scale_mat': scale_mat,
            }
            np.savez('{0}/cameras_gt_{1}.npz'.format(evaldir, epoch), **gt_camera_poses)
            np.savez('{0}/cameras_pred_{1}.npz'.format(evaldir, epoch), **pred_camera_poses)

        return

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--conf', type=str, default='./confs/dtu_fixed_cameras.conf')
    parser.add_argument('--expname', type=str, default='', help='The experiment name to be evaluated.')
    parser.add_argument('--exps_folder', type=str, default='exps', help='The experiments folder name.')
    parser.add_argument('--gpu', type=str, default='auto', help='GPU to use [default: GPU auto]')
    parser.add_argument('--timestamp', default='latest', type=str, help='The experiemnt timestamp to test.')
    parser.add_argument('--checkpoint', default='latest',type=str,help='The trained model checkpoint to test')
    parser.add_argument('--scan_id', type=str, default='-1', help='If set, taken to be the scan id.')
    parser.add_argument('--resolution', default=512, type=int, help='Grid resolution for marching cube')
    parser.add_argument('--is_uniform_grid', default=False, action="store_true", help='If set, evaluate marching cube with uniform grid.')
    parser.add_argument('--eval_cameras', default=False, action="store_true", help='If set, evaluate camera accuracy of trained cameras.')
    parser.add_argument('--eval_rendering', default=False, action="store_true", help='If set, evaluate rendering quality.')

    opt = parser.parse_args()

    if opt.gpu == "auto":
        deviceIDs = GPUtil.getAvailable(order='memory', limit=1, maxLoad=0.5, maxMemory=0.5, includeNan=False, excludeID=[], excludeUUID=[])
        gpu = deviceIDs[0]
    else:
        gpu = opt.gpu

    if (not gpu == 'ignore'):
        os.environ["CUDA_VISIBLE_DEVICES"] = '{0}'.format(gpu)

    evaluate(conf=opt.conf,
             expname=opt.expname,
             exps_folder_name=opt.exps_folder,
             evals_folder_name='evals',
             timestamp=opt.timestamp,
             checkpoint=opt.checkpoint,
             scan_id=opt.scan_id,
             resolution=opt.resolution,
             eval_cameras=opt.eval_cameras,
             eval_rendering=opt.eval_rendering
             )
