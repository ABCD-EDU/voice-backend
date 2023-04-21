from pydub import AudioSegment
from pydub.utils import make_chunks
from pydub import AudioSegment
import os


def split(audio_segment):
    interval = 8 * 1000  # 8 seconds in milliseconds
    chunks = make_chunks(audio_segment, interval)

    return chunks


def compile(input_path: str, output_path: str):
    output_audio = AudioSegment.empty()
    file_count = len([f for f in os.listdir(input_path)
                      if os.path.isfile(os.path.join(input_path, f))])

    for i in range(file_count):
        chunk = AudioSegment.from_file(
            f"{input_path}/chunk_{i}.wav", format="wav")
        output_audio += chunk

    output_audio.export(f"{output_path}/output.wav", format="wav")
