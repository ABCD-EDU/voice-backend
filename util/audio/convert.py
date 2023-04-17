from pydub import AudioSegment
from io import BytesIO


def convert_to_mp3(audio_file):
    audio = AudioSegment.from_file(BytesIO(audio_file))
    buffer = BytesIO()
    audio.export(buffer, format="mp3", bitrate="8k")
    buffer.seek(0)
    return buffer
