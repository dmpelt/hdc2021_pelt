import argparse

parser = argparse.ArgumentParser(description='Apply trained networks for HDC2021 competition.')
parser.add_argument('infolder', type=str, help="Folder where the input image files are located")
parser.add_argument('outfolder', type=str, help="Folder where the output images must be stored")
parser.add_argument('category', type=int, help="Blur category number. Values between 0 and 19")
args = parser.parse_args()

indir = args.infolder
outdir = args.outfolder
cat = args.category
if cat<0 or cat>19:
    raise ValueError('Blur category must be between 0 and 19 (inclusive).')

import msdnet
import skimage.transform as st
import imageio
import os
import numpy as np
from pathlib import Path

infiles = sorted(Path(indir).glob('*.tif'))

os.makedirs(outdir, exist_ok=True)

bd = Path('trainednets/category{}'.format(cat))

mnim = imageio.imread('trainednets/inputmeans/category{}.png'.format(cat))

n20 = msdnet.network.MSDNet.from_file(str(bd / 'regr_params20.h5'))
n10 = msdnet.network.MSDNet.from_file(str(bd / 'regr_params10.h5'))
n4 = msdnet.network.MSDNet.from_file(str(bd / 'regr_params4.h5'))
n2 = msdnet.network.MSDNet.from_file(str(bd / 'regr_params2.h5'))
n = msdnet.network.MSDNet.from_file(str(bd / 'regr_paramsf.h5'))

for f in infiles:
    im = imageio.imread(str(f)).astype(np.float32) - mnim
    im20 = st.downscale_local_mean(im, (20, 20))
    im10 = st.downscale_local_mean(im, (10, 10))
    im4 = st.downscale_local_mean(im, (4, 4))
    im2 = st.downscale_local_mean(im, (2, 2))

    out20 = n20.forward(im20[None].copy())

    inp = np.zeros((2, im10.shape[0], im10.shape[1]), dtype=np.float32)
    inp[0] = im10
    inp[1] = st.rescale(out20[0], 2)
    out10 = n10.forward(inp)

    inp = np.zeros((2, im4.shape[0], im4.shape[1]), dtype=np.float32)
    inp[0] = im4
    inp[1] = st.rescale(out10[0], 2.5)
    out4 = n4.forward(inp)

    inp = np.zeros((2, im2.shape[0], im2.shape[1]), dtype=np.float32)
    inp[0] = im2
    inp[1] = st.rescale(out4[0], 2)
    out2 = n2.forward(inp)

    inp = np.zeros((2, im.shape[0], im.shape[1]), dtype=np.float32)
    inp[0] = im
    inp[1] = st.rescale(out2[0], 2)
    out = n.forward(inp)

    out[out<0]=0
    out[out>1]=1
    imageio.imsave(str(Path(outdir) / f.stem) + '.png', (out[0]*255).astype(np.uint8))
