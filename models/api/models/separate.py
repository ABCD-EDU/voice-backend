from fastapi import APIRouter, HTTPException
from io import BytesIO
from pydub import AudioSegment

import util.models.speech_separation.inference.main as separate
from util.db.client import get_db
from util.kafka.producer import KafkaProducerSingleton
from util.minio.client import get_minio_client

router = APIRouter()


@router.post("/", status_code=201)
async def get_results(id: str, speaker_count: int, mode: str):
    if id == None:
        raise HTTPException(
            status_code=500, detail="Request ID is required"
        )

    bucket_to = "separated-audio" if speaker_count == 2 else "3-speaker-separated-audio"
    bucket_to = "sota-" + bucket_to if mode == "sota" else bucket_to

    producer = KafkaProducerSingleton.getInstance().producer
    minio = get_minio_client()

    # TODO: Kafka Producer Events
    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
        "process": "SEPARATION", "status": "PROCESSING"})

   # TODO: Call DB for num_chunks
    try:
        cursor = get_db().cursor()
        query = "SELECT num_chunks FROM requests WHERE filename = %s;"
        values = (id,)

        cursor.execute(query, values)

        rows = cursor.fetchone()
        num_chunks = rows[0]
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "SEPARATION", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with retrieving item in MySQL")

    # SEPARATE AUDIO SPEAKERS
    try:
      for chunk in range(num_chunks):
          chunk_index = chunk+1
          object_data = minio.get_object(
              "audio-chunks",
              f"{id}-{chunk_index}.wav"
          )
          object_content = object_data.read()
          audio_data = BytesIO(object_content)
          print(audio_data)
          print("speaker count", speaker_count)
          audio_outputs = separate.run(audio_bytes=audio_data, speaker_count=speaker_count, mode=mode)
          print("sep don")

          # TODO: Bucket writes
          print("OUTPUTS", audio_outputs)
          for speaker in range(len(audio_outputs)):
              audio_outputs[speaker].seek(0)
              audio_test = AudioSegment.from_file(audio_outputs[speaker])
              output_test = BytesIO()
              audio_test.export(output_test, format="wav", bitrate="8k")
              output_test.seek(0)

              print("FOR CHUNK:", chunk, "SPEAKER:", audio_outputs[speaker], "LENGTH:", len(
                  audio_outputs[speaker].getvalue()), "INDEX:", speaker+1, "OUTPUT TO:","separated-audio" if speaker_count == 2 else "3-speaker-separated-audio")
              minio.put_object(
                  bucket_name= bucket_to,
                  object_name=f"{id}-{chunk_index}-{speaker + 1}.wav",
                  data=output_test,
                  length=len(output_test.getvalue())
              )
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "SEPARATION", "status": "FAILED"})
        raise HTTPException(status_code="500", detail="Problem with retrieving item in MinIO bucket")

    # TODO: DB Update writes
    try:
        cursor = get_db().cursor()
        query = """
          UPDATE requests
          SET status = %s
          WHERE filename = %s;
        """
        values = ("TWO_SPEAKERS_SEPARATED" if speaker_count == 2 else "THREE_SPEAKERS_SEPARATED",id)

        cursor.execute(query, values)
        get_db().commit()
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "SEPARATION", "status": "FAILED"})
        raise HTTPException(status_code="500",
                            detail="Problem with retrieving item in MySQL")

    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
        "process": "SEPARATION", "status": "SUCCESS"})

    return id