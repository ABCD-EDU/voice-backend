from fastapi import APIRouter, HTTPException
from pydub import AudioSegment
from io import BytesIO

from util.kafka.producer import KafkaProducerSingleton
import util.minio.client as minio
import util.audio.split as split
import util.db.client as db

router = APIRouter()


@router.post("", status_code=201)
async def split_audio(id: str):
    if id == None or id == "":
        raise HTTPException(
            status_code=500, detail="Request ID is required"
        )

    producer = KafkaProducerSingleton.getInstance().producer

    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
                  "process": "CHUNKED", "status": "PROCESSING"})

    try:
        minio_client = minio.get_minio_client()
        data = minio_client.get_object(
            "input-audio",
            f"{id}.wav",
        )
        content = data.read()
        chunks = split.split(AudioSegment.from_file(BytesIO(content)))
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "CHUNKED", "status": "FAILED"})
        raise HTTPException(status_code="500", detail="Problem with retrieving item in MinIO bucket")

    try:
      for i, chunk in enumerate(chunks):
          output_buffer = BytesIO()
          chunk.export(output_buffer, format="wav")
          output_buffer.seek(0)

          object_name = f"{id}-{i+1}.wav"
          minio_client.put_object(
              bucket_name='audio-chunks',
              object_name=object_name,
              data=output_buffer,
              length=output_buffer.getbuffer().nbytes
          )
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "CHUNKED", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with putting item in MinIO")

    try:
        cursor = db.get_db().cursor()
        query = """
          UPDATE requests SET STATUS=%s, num_chunks=%s WHERE filename=%s
        """
        values = ("CHUNKED", len(chunks), f"{id}")

        cursor.execute(query, values)
        db.get_db().commit()
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "CHUNKED", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Something went wrong with writing results to DB")

    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
                  "process": "CHUNKED", "status": "SUCCESS"})

    return id