from pydub import AudioSegment
import io


def compile(audio1, audio2):
    # create AudioSegment objects from the audio data
    audio1_segment = AudioSegment.from_file(audio1, format="wav")
    audio2_segment = AudioSegment.from_file(audio2, format="wav")

    # concatenate the audio segments
    combined_segment = audio1_segment + audio2_segment

    # export the combined audio as a new BytesIO object
    combined_audio = io.BytesIO()
    combined_segment.export(combined_audio, format='wav')
    test = AudioSegment.from_file(combined_audio, format="wav")
    test_out = io.BytesIO()
    test.export(test_out, format="wav")

    return test_out

def compile_many(audio_segments):
    # create AudioSegment object from the first segment
    combined_segment = AudioSegment.from_file(audio_segments[0], format="wav")

    # concatenate the remaining audio segments
    for audio_segment in audio_segments[1:]:
        combined_segment += AudioSegment.from_file(audio_segment, format="wav")

    # export the combined audio as a new BytesIO object
    combined_audio = io.BytesIO()
    combined_segment.export(combined_audio, format='wav')

    return combined_audio