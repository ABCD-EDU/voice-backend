from pyannote.audio import Pipeline
import numpy as np
import soundfile as sf
import librosa
import soundfile as sf
import torch
import io

pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1",
                                    use_auth_token="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")


def collect_tstamps(diarization):
    timestamps = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        print(f"speaker_{speaker}", turn.start, turn.end)
        timestamps.append([f"{speaker}", turn.start, turn.end])
    return timestamps


def produce_audio_for_sep_speakers(y, sr, timestamps):
    speaker1_speech = np.array([])
    speaker2_speech = np.array([])
    speaker2_start = 0
    for i in range(len(timestamps) - 1, -1, -1):
        print(i)
        start = int(float(timestamps[i][1]) * sr)
        end = int(float(timestamps[i][2]) * sr)
        if timestamps[i][0] == 'SPEAKER_00':
            speaker1_speech = np.concatenate(
                (speaker1_speech, y[0:speaker2_start]), axis=None)
            print("speaker1", start, end)
        else:
            print("speaker2", start, end)
            speaker2_start = start
            speaker2_speech = np.concatenate(
                (speaker2_speech, y[start:end]), axis=None)

    sf.write('results/speaker1.wav', speaker1_speech, sr)
    sf.write('results/speaker2.wav', speaker2_speech, sr)

    audio1_bytes = io.BytesIO()
    audio2_bytes = io.BytesIO()

    sf.write(audio1_bytes, speaker1_speech, sr, format="wav")
    sf.write(audio2_bytes, speaker2_speech, sr, format="wav")
    return [audio1_bytes, audio2_bytes]


def run(audio_input):
    # waveform, sample_rate = torchaudio.load(audio_input)
    audio, sample_rate = librosa.load(audio_input, sr=None, mono=True)

    audio_tensor = torch.from_numpy(audio[np.newaxis, :])

    audio_in_memory = {"waveform": audio_tensor, "sample_rate": sample_rate}

    # audio_in_memory = {"waveform": waveform, "sample_rate": sample_rate}
    diarization = pipeline(audio_in_memory,
                           num_speakers=2, max_speakers=2)
    timestamps = collect_tstamps(diarization)
    return produce_audio_for_sep_speakers(audio, sample_rate, timestamps)
