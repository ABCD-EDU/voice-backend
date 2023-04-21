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
