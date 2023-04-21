from pydub import AudioSegment
from io import BytesIO
import librosa
import torchaudio


def convert_to_wav(audio_file):
    # audio = AudioSegment.from_file(BytesIO(audio_file))
    # audio.set_frame_rate(8000)
    # audio.set_sample_width(1)
    # buffer = BytesIO()
    # audio.export(buffer, format="mp3", bitrate="256k")

    audio, sr = librosa.load(audio_file, sr=8000, format="wav")
    print("test", sr)
    # buffer.seek(0)
    # return buffer
    return audio
