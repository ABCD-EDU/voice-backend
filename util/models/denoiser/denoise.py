import librosa
import noisereduce as nr

# Specify the directory containing the noisy wav files
def run(audio_stream):
   # Get a list of all WAV files in the directory
   reduced_noise = nr.reduce_noise(y=audio_stream, sr=8000)

   return reduced_noise