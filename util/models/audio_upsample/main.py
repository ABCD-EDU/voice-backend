from lightning_model import NuWave
from omegaconf import OmegaConf as OC
import os
import argparse
import datetime
from glob import glob
import torch
import librosa as rosa
from scipy.io.wavfile import write as swrite
from utils.stft import STFTMag
import numpy as np
from filters import LowPass
from datetime import datetime

def run(input_path:str, output_path:str):
    device='cuda'
    no_init_noise=True,
    steps = None
    hparams = OC.load('hparameter.yaml')
    if steps is not None:
        hparams.ddpm.max_step = steps
        hparams.ddpm.noise_schedule = \
                "torch.tensor([1e-6,2e-6,1e-5,1e-4,1e-3,1e-2,1e-1,9e-1])"
    else:
        steps = hparams.ddpm.max_step
    model = NuWave(hparams).to(device)
    # start timer
    startTime = datetime.now()
    ckpt_path = os.path.join(hparams.log.checkpoint_dir, "latest_checkpoint.ckpt")
    ckpt = torch.load(ckpt_path, map_location='cpu')
    model.load_state_dict(ckpt['state_dict'] if not('EMA' in ckpt_path) else ckpt)
    wav, _ = rosa.load(input_path, sr=hparams.audio.sr, mono=True)
    wav = torch.Tensor(wav).unsqueeze(0).to(device)
    
    lp = LowPass(ratio = [1/2]).to(device)
    wav = lp(wav, 0)

    upsampled = model.sample(wav, hparams.ddpm.max_step, no_init_noise,
                             True)

    for i, uwav in enumerate(upsampled):
        t = hparams.ddpm.max_step - i
        if t != 0:
            continue
        swrite(f'{output_path}',
               hparams.audio.sr, uwav[0].detach().cpu().numpy())

    print(datetime.now() - startTime, startTime, datetime.now())

if __name__ == "__main__":
    run(input_path="sepformer_out.wav", output_path="latest_test_x3")
    