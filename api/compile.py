from fastapi import APIRouter, HTTPException
from io import BytesIO

from util.audio.compile import compile_many
from util.db.client import get_db
from util.minio.client import get_minio_client
from util.models.audio_upsample.main import run as upsample
from util.kafka.producer import KafkaProducerSingleton


router = APIRouter()


@router.post("", status_code=201)
async def run(id: str):
    if id == None:
        raise HTTPException(
            status_code=500, detail="Request ID is required"
        )

    minio = get_minio_client()
    producer = KafkaProducerSingleton.getInstance().producer
    # TODO: Add Kafka Event Producers
    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
        "process": "UPSAMPLING", "status": "PROCESSING"})

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
            "process": "UPSAMPLING", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with retrieving item in MySQL")

    audio1_segments = []
    audio2_segments = []
    try:
      print("GETTING ITEMS FROM BUCKET")
      # TODO: Get chunks from MinIO bucket (audio-chunks)
      for chunk in range(num_chunks):
          chunk_index = chunk + 1
          for i in range(2):
              print("RETRIEVING", f"{id}-{chunk_index}-{i+1}.wav")

              object_data = minio.get_object(
                  bucket_name="upsampled-audio",
                  object_name=f"{id}-{chunk_index}-{i+1}.wav",
              )
              object_content = object_data.read()
              audio_bytes = BytesIO(object_content)

              if i == 0:
                  audio1_segments.append(audio_bytes)
              else:
                  audio2_segments.append(audio_bytes)
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with retrieving item in MinIO")

    audio1 = compile_many(audio1_segments)
    audio2 = compile_many(audio2_segments)
    try:
        for i in range(2):
            minio.put_object(
                bucket_name="recompiled-audio",
                object_name=f"{id}-{i}.wav",
                data=audio1 if i == 1 else audio2,
                length=len(audio1.getvalue() if i == 1 else audio2.getvalue())
            )
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with putting item in MinIO")
