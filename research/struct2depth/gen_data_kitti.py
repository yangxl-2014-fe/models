
# Copyright 2018 The TensorFlow Authors All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

""" Offline data generation for the KITTI dataset.
wget https://raw.githubusercontent.com/mrharicot/monodepth/master/utils/kitti_archives_to_download.txt
# https://github.com/mrharicot/monodepth/blob/master/utils/kitti_archives_to_download.txt
wget -i kitti_archives_to_download.txt
unzip "*.zip"
"""

import logging
import os
import os.path as osp
from absl import app
from absl import flags
from absl import logging
import numpy as np
import cv2
import os, glob
import time

import alignment
from alignment import compute_overlap
from alignment import align
from color_print import ColorPrint


SEQ_LENGTH = 3
WIDTH = 416
HEIGHT = 128
STEPSIZE = 1
# INPUT_DIR = '/usr/local/google/home/anelia/struct2depth/KITTI_FULL/kitti-raw-uncompressed'
# OUTPUT_DIR = '/usr/local/google/home/anelia/struct2depth/KITTI_procesed/'

INPUT_DIR = '/disk4t0/0-MonoDepth-Database/KITTI_MINI/'
OUTPUT_DIR = '/disk4t0/0-MonoDepth-Database/KITTI_MINI_processed/'


def get_line(file, start):
    file = open(file, 'r')
    lines = file.readlines()
    lines = [line.rstrip() for line in lines]
    ret = None
    for line in lines:
        nline = line.split(': ')
        if nline[0]==start:
            ret = nline[1].split(' ')
            ret = np.array([float(r) for r in ret], dtype=float)
            ret = ret.reshape((3,4))[0:3, 0:3]
            break
    file.close()
    return ret


def crop(img, segimg, fx, fy, cx, cy):
    # Perform center cropping, preserving 50% vertically.
    middle_perc = 0.50
    left = 1-middle_perc
    half = left/2
    a = img[int(img.shape[0]*(half)):int(img.shape[0]*(1-half)), :]
    aseg = segimg[int(segimg.shape[0]*(half)):int(segimg.shape[0]*(1-half)), :]
    cy /= (1/middle_perc)

    # Resize to match target height while preserving aspect ratio.
    wdt = int((128*a.shape[1]/a.shape[0]))
    x_scaling = float(wdt)/a.shape[1]
    y_scaling = 128.0/a.shape[0]
    b = cv2.resize(a, (wdt, 128))
    bseg = cv2.resize(aseg, (wdt, 128))

    # Adjust intrinsics.
    fx*=x_scaling
    fy*=y_scaling
    cx*=x_scaling
    cy*=y_scaling

    # Perform center cropping horizontally.
    remain = b.shape[1] - 416
    cx /= (b.shape[1]/416)
    c = b[:, int(remain/2):b.shape[1]-int(remain/2)]
    cseg = bseg[:, int(remain/2):b.shape[1]-int(remain/2)]

    return c, cseg, fx, fy, cx, cy


def run_all():
  ct = 0
if not OUTPUT_DIR.endswith('/'):
    OUTPUT_DIR = OUTPUT_DIR + '/'

img_num_generated = 0
time_beg = time.time()

for d in glob.glob(INPUT_DIR + '/*/'):
    date = d.split('/')[-2]
    file_calibration = d + 'calib_cam_to_cam.txt'
    calib_raw = [get_line(file_calibration, 'P_rect_02'), get_line(file_calibration, 'P_rect_03')]

    for d2 in glob.glob(d + '*/'):
        seqname = d2.split('/')[-2]
        print('Processing sequence', seqname)
        for subfolder in ['image_02/data', 'image_03/data']:
            ct = 1
            seqname = d2.split('/')[-2] + subfolder.replace('image', '').replace('/data', '')
            if not os.path.exists(OUTPUT_DIR + seqname):
                # os.mkdir(OUTPUT_DIR + seqname)
                os.makedirs(OUTPUT_DIR + seqname)

            calib_camera = calib_raw[0] if subfolder=='image_02/data' else calib_raw[1]
            folder = d2 + subfolder
            files = glob.glob(folder + '/*.png')
            files = [file for file in files if not 'disp' in file and not 'flip' in file and not 'seg' in file]
            files = sorted(files)

            files_seg = glob.glob(folder + '/*.png')
            files_seg = [file for file in files_seg if 'seg' in file]
            files_seg = sorted(files_seg)

            if len(files) != len(files_seg):
                print('files:     {}'.format(len(files)))
                print('files_seg: {}'.format(len(files_seg)))
                raise ValueError

            enable_debug = True
            if enable_debug:
                '''
                print('files: {}'.format(len(files)))
                for item_f in files:
                    print('  - {}'.format(item_f))
                '''
                data_dir, _ = osp.split(files_seg[0])
                ColorPrint.print_warn('- process_dir: {}'.format(data_dir))
                ColorPrint.print_warn('- files_seg:   {}'.format(len(files_seg)))
                for item_f in files_seg:
                    ColorPrint.print_info('  - {}'.format(item_f))

            for i in range(SEQ_LENGTH, len(files)+1, STEPSIZE):
                imgnum = str(ct).zfill(10)
                if os.path.exists(OUTPUT_DIR + seqname + '/' + imgnum + '.png'):
                    ct+=1
                    continue
                big_img = np.zeros(shape=(HEIGHT, WIDTH*SEQ_LENGTH, 3))
                big_img_seg = np.zeros(shape=(HEIGHT, WIDTH * SEQ_LENGTH, 3))
                wct = 0

                for j in range(i-SEQ_LENGTH, i):  # Collect frames for this sample.
                    img = cv2.imread(files[j])
                    img_seg = cv2.imread(files_seg[j])
                    ORIGINAL_HEIGHT, ORIGINAL_WIDTH, _ = img.shape

                    if img.shape != img_seg.shape:
                        print('img.shape:     {}'.format(img.shape))
                        print('img_seg.shape: {}'.format(img_seg.shape))
                        raise ValueError

                    zoom_x = WIDTH/ORIGINAL_WIDTH
                    zoom_y = HEIGHT/ORIGINAL_HEIGHT

                    # Adjust intrinsics.
                    calib_current = calib_camera.copy()
                    calib_current[0, 0] *= zoom_x
                    calib_current[0, 2] *= zoom_x
                    calib_current[1, 1] *= zoom_y
                    calib_current[1, 2] *= zoom_y

                    calib_representation = ','.join([str(c) for c in calib_current.flatten()])

                    img = cv2.resize(img, (WIDTH, HEIGHT))
                    big_img[:,wct*WIDTH:(wct+1)*WIDTH] = img

                    img_seg = cv2.resize(img_seg, (WIDTH, HEIGHT))
                    big_img_seg[:, wct * WIDTH:(wct + 1) * WIDTH] = img_seg

                    wct+=1
                cv2.imwrite(OUTPUT_DIR + seqname + '/' + imgnum + '.png', big_img)
                cv2.imwrite(OUTPUT_DIR + seqname + '/' + imgnum + '-fseg.png', big_img_seg)
                img_num_generated += 1

                f = open(OUTPUT_DIR + seqname + '/' + imgnum + '_cam.txt', 'w')
                f.write(calib_representation)
                f.close()
                ct+=1


time_end = time.time()
ColorPrint.print_warn('process {} images in total.'.format(img_num_generated))
ColorPrint.print_warn('elapsed {} seconds.'.format(time_end - time_beg))


def main(_):
  run_all()


if __name__ == '__main__':
  app.run(main)
