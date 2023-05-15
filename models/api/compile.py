from fastapi import APIRouter, HTTPException
from io import BytesIO

from util.audio.compile import compile_many
from util.db.client import get_db
from util.minio.client import get_minio_client
from util.models.audio_upsample.main import run as upsample
from util.kafka.producer import KafkaProducerSingleton


router = APIRouter()


@router.post("", status_code=201)
async def run(id: str, from_bucket: str, to_bucket: str, speaker_count: int):
    if id == None:
        raise HTTPException(
            status_code=500, detail="Request ID is required"
        )

    minio = get_minio_client()
    producer = KafkaProducerSingleton.getInstance().producer
    # TODO: Add Kafka Event Producers
    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
        "process": "RECOMPILED", "status": "PROCESSING"})

    # TODO: Call DB for num_chunks
    try:
        cursor = get_db().cursor()
        query = "SELECT num_chunks FROM requests WHERE filename = %s;"
        values = (id,)

        cursor.execute(query, values)
        get_db().commit()

        rows = cursor.fetchone()
        num_chunks = rows[0]
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "RECOMPILED", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with retrieving item in MySQL")

    audio_segments = [[],[],[]]
    try:
      print("GETTING ITEMS FROM BUCKET")
      # TODO: Get chunks from MinIO bucket (audio-chunks)
      for chunk in range(num_chunks):
          chunk_index = chunk + 1
          for speaker_i in range(speaker_count):
              print("RETRIEVING", f"{id}-{chunk_index}-{speaker_i+1}.wav from {from_bucket}")

              object_data = minio.get_object(
                  bucket_name=from_bucket,
                  object_name=f"{id}-{chunk_index}-{speaker_i+1}.wav",
              )
              object_content = object_data.read()
              audio_bytes = BytesIO(object_content)

              audio_segments[speaker_i].append(audio_bytes)
              print("AUDIO SEGMENTS:",audio_segments)
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "RECOMPILED", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with retrieving item in MinIO")

    audio_compiled = []
    for speaker_i in range(speaker_count):
        if len(audio_segments[speaker_i]) != 0:
           audio_compiled.append(compile_many(audio_segments[speaker_i]))
           print("AUDIO COMPILED:", audio_compiled)

    # TODO: PUT ITEMS BACK IN BUCKET
    try:
      for audio_i in range(len(audio_compiled)):
          print("PUTTING", f"{id}-{chunk_index}-{audio_i+1}.wav from {to_bucket}", "AUDIO:", audio_compiled[audio_i], "LENGTH:", len(audio_compiled[audio_i].getvalue()))

          minio.put_object(
              bucket_name=to_bucket,
              object_name=f"{id}-{audio_i+1}.wav",
              data=audio_compiled[audio_i],
              length=len(audio_compiled[audio_i].getvalue())
          )
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "RECOMPILED", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with putting item in MinIO")

    # TODO: Write DB Status Update
    try:
        print("UPDATING STATUS FROM DB")
        cursor = get_db().cursor()
        query = """
          UPDATE requests
          SET status = 'COMPLETED'
          WHERE filename = %s;
        """
        values = (id,)

        cursor.execute(query, values)
        get_db().commit()
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "RECOMPILED", "status": "FAILED"})
        return HTTPException(status_code=500, detail="Problem with updating item in MySQL")

    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "RECOMPILED", "status": "SUCCESS"})

    return id
