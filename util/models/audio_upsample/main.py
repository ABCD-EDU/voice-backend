from util.models.audio_upsample.lightning_model import NuWave
from omegaconf import OmegaConf as OC
import os
import argparse
import datetime
from glob import glob
import torch
import librosa as rosa
from scipy.io.wavfile import write as swrite
from util.models.audio_upsample.utils.stft import STFTMag
import numpy as np
from util.models.audio_upsample.filters import LowPass
from datetime import datetime
from io import BytesIO

device = 'cuda'
no_init_noise = True,
steps = None
hparams = OC.load('util/models/audio_upsample/hparameter.yaml')
if steps is not None:
    hparams.ddpm.max_step = steps
    hparams.ddpm.noise_schedule = \
        "torch.tensor([1e-6,2e-6,1e-5,1e-4,1e-3,1e-2,1e-1,9e-1])"
else:
    steps = hparams.ddpm.max_step
model = NuWave(hparams).to(device)

ckpt_path = os.path.join(hparams.log.checkpoint_dir,
                         "latest_checkpoint.ckpt")
ckpt = torch.load(ckpt_path, map_location='cpu')
model.load_state_dict(ckpt['state_dict'] if not (
    'EMA' in ckpt_path) else ckpt)

lp = LowPass(ratio=[1/2]).to(device)
print("MODEL LOADED")


def run(audio_bytes: BytesIO):
    wav, _ = rosa.load(audio_bytes, sr=hparams.audio.sr, mono=True)
    wav = torch.Tensor(wav).unsqueeze(0).to(device)
    print("LOADING AUDIO FILES")

    wav = lp(wav, 0)
    print("LOW PASS DONE")

    upsampled = model.sample(wav, hparams.ddpm.max_step, no_init_noise,
                             True)

    print("UPSAMPLING DONE")

    audio_buffer = BytesIO()
    for i, uwav in enumerate(upsampled):
        t = hparams.ddpm.max_step - i
        if t != 0:
            continue
        swrite(audio_buffer,
               hparams.audio.sr, uwav[0].detach().cpu().numpy())
    print("SAVING TO BUFFER DONE")

    return audio_buffer
