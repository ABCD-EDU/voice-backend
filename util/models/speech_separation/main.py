# from util.minio.client import get_minio_client
import librosa
import numpy as np
from pydub import AudioSegment
import soundfile as sf
import torch
import speechbrain as sb
from speechbrain.dataio.dataio import read_audio
from tqdm import tqdm
from hyperpyyaml import load_hyperpyyaml
from speechbrain.utils.distributed import run_on_main
import speechbrain as sb
import os
from io import BytesIO
import torch
import torch.nn.functional as F
import torchaudio
torchaudio.set_audio_backend("soundfile")
# Define training procedure


class Separation(sb.Brain):
    def compute_forward(self, mix, noise=None):
        """Forward computations from the mixture to the separated signals."""

        # Unpack lists and put tensors in the right device
        # mix, mix_lens = mix
        # mix, mix_lens = mix.to(self.device), mix_lens.to(self.device)
        mix = mix.to(self.device)
    # Separation
        mix_w = self.hparams.Encoder(mix)
        est_mask = self.hparams.MaskNet(mix_w)
        mix_w = torch.stack([mix_w] * self.hparams.num_spks)
        sep_h = mix_w * est_mask

        # Decoding
        est_source = torch.cat(
            [
                self.hparams.Decoder(sep_h[i]).unsqueeze(-1)
                for i in range(self.hparams.num_spks)
            ],
            dim=-1,
        )

        # T changed after conv1d in encoder, fix it here
        T_origin = mix.size(1)
        T_est = est_source.size(1)
        if T_origin > T_est:
            est_source = F.pad(est_source, (0, 0, 0, T_origin - T_est))
        else:
            est_source = est_source[:, :T_origin, :]

        return est_source

    audio_files = []

    def save_audio(self, predictions):
        audio_outputs = []
        for ns in range(int(self.hparams.num_spks)):
            # Estimated source
            signal = predictions[0, :, ns]
            signal = signal / signal.abs().max()

            # Exports audio to bytes format
            audio_data = BytesIO()
            torchaudio.save(
                audio_data, signal.unsqueeze(0).cpu(), self.hparams.sample_rate, format="wav"
            )
            audio_outputs.append(audio_data)
        return audio_outputs

    def save_local(self, predictions, output_path):
        # print(self.hparams)
        for ns in range(int(self.hparams.num_spks)):
            # Estimated source
            signal = predictions[0, :, ns]
            signal = signal / signal.abs().max()
            save_file = os.path.join(
                f"{output_path}", "source{}hat.wav".format(ns + 1)
            )
            torchaudio.save(
                save_file, signal.unsqueeze(0).cpu(), self.hparams.sample_rate
            )


def run(audio_bytes: BytesIO):
    # TODO: Load from MinIO instead of local path
    mix_audio, sr = librosa.load(audio_bytes, sr=8000, mono=True)

    tensor = torch.from_numpy(np.expand_dims(mix_audio, axis=0)).float()
    with torch.no_grad():
        predictions = separator.compute_forward(
            mix=tensor[0].unsqueeze(0))
    print("compute forward loaded")

    # TODO: EXPORT TO BUCKET INSTEAD
    print("separation processing")
    # separator.save_local(predictions=predictions, output_path='results')
    return separator.save_audio(predictions=predictions)


# Load hyperparameters file with command-line overrides
# hparams_file, run_opts, overrides = sb.parse_arguments(sys.argv[1:])
hparams_file, run_opts, overrides = sb.parse_arguments(
    ["util/models/speech_separation/hyperparams.yaml"])
with open(hparams_file) as fin:
    hparams = load_hyperpyyaml(fin, overrides)
print("hparams loaded")
# Load pretrained model if pretrained_separator is present in the yaml
if "pretrained_separator" in hparams:
    run_on_main(hparams["pretrained_separator"].collect_files)
    hparams["pretrained_separator"].load_collected(
        device=run_opts["device"]
    )
print("pretrained separator loaded")
# Brain class initialization
separator = Separation(
    modules=hparams["modules"],
    hparams=hparams,
    run_opts=run_opts,
)
print("brain class loaded")
