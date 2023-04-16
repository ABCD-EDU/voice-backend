from speechbrain.dataio.dataio import read_audio
import logging
from tqdm import tqdm
from hyperpyyaml import load_hyperpyyaml
from speechbrain.utils.distributed import run_on_main
import speechbrain as sb
import os
import sys
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

    def save_audio(self, predictions, output_path):
        for ns in range(int(self.hparams.num_spks)):
            # Estimated source
            signal = predictions[0, :, ns]
            signal = signal / signal.abs().max()
            save_file = os.path.join(
                f"{output_path}", "source_{}_hat.wav".format(ns + 1)
            )
            torchaudio.save(
                save_file, signal.unsqueeze(0).cpu(), self.hparams.sample_rate
            )

# TODO: use input_path, output_path instead of static paths


def run(input_path: str, output_path: str):
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
    mix_audio = read_audio("util/models/speech_separation/test_mix_2.wav")
    print("mix audio loaded")
    with torch.no_grad():
        predictions = separator.compute_forward(mix=mix_audio.unsqueeze(0))

    print("compute forward loaded")

    separator.save_audio(predictions=predictions,
                         output_path="util/models/speech_separation/results")
    print("done separation")
