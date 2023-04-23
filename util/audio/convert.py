from pydub import AudioSegment
from io import BytesIO
import librosa


def convert_to_wav(audio_file):
    audio, sr = librosa.load(audio_file, sr=8000, format="wav")
    return audio
