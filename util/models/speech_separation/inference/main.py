from io import BytesIO
from speechbrain.pretrained import SepformerSeparation as separator
import torchaudio
import gdown

import librosa
import os
import requests
import torch
import numpy as np

def download_file(url, folder_path):
   if not os.path.exists(folder_path):
      os.makedirs(folder_path)

   file_id = url.split("/")[-2]
   filename = url.split("/")[-1]
   file_path = os.path.join(folder_path, filename)

   if os.path.exists(file_path):
      print("File already exists.")
      return

   download_url = f"https://drive.google.com/uc?id={file_id}"
   gdown.download(download_url, file_path, quiet=False)

# Example usage
folder_path = "ckpt_2_speakers"
url = "https://drive.google.com/drive/folders/17H9gpFsCBkUy2ZNRyi5YM8FSkRPUdPDR?usp=share_link"
# download_file(url, folder_path)
folder_path = "ckpt_3_speakers"
url = "https://drive.google.com/drive/folders/1TfF491bHXKuZ39GjzDcoqjo1jZnNqcYW?usp=share_link"
# download_file(url, folder_path)

model_2speakers = separator.from_hparams(source="speechbrain/sepformer-libri2mix", savedir='ckpt_2_speakers',run_opts={"device":"cuda"})
model_3speakers = separator.from_hparams(source="speechbrain/sepformer-libri3mix", savedir='ckpt_3_speakers',run_opts={"device":"cuda"})

def run(audio_bytes: BytesIO, speaker_count: int):
  print("start run")
  mix_audio, sr = librosa.load(audio_bytes, sr=8000)
  print("loaded librosa")
  tensor = torch.from_numpy(np.expand_dims(mix_audio, axis=0)).float()
  print("loaded to torch")
  est_sources = 0
  if speaker_count == 2:
    print("trying to separate batch")
    with torch.no_grad():
      print("inside torch nograd")
      est_sources = model_2speakers.forward(mix=tensor[0].unsqueeze(0))
  if speaker_count == 3:
    est_sources = model_3speakers.forward(mix=tensor[0].unsqueeze(0))
    print("est source produced")
    speaker_3 = BytesIO()
    print("bytes 3 ")
    signal_3 = est_sources[0, :, 2]
    print("assigned")
    signal_3 = signal_3 / signal_3.abs().max()
    print("math")
    torchaudio.save(speaker_3, signal_3.unsqueeze(0).detach().cpu(), 8000, format="wav")
    print("saved")

  print(est_sources)

  signal_1 = est_sources[0, :, 0]
  signal_1 = signal_1 / signal_1.abs().max()
  signal_2 = est_sources[0, :, 1]
  signal_2 = signal_2 / signal_2.abs().max()
  speaker_1 = BytesIO()
  torchaudio.save(speaker_1, signal_1.unsqueeze(0).detach().cpu(), 8000, format="wav")
  speaker_2 = BytesIO()
  torchaudio.save(speaker_2, signal_2.unsqueeze(0).detach().cpu(), 8000, format="wav")

  if speaker_count == 2:
    return [speaker_1, speaker_2]
  elif speaker_count == 3:
    return [speaker_1, speaker_2, speaker_3]
  else:
    raise "Speaker Count must be 2 or 3"
