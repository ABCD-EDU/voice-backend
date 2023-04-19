from fastapi import APIRouter, HTTPException
from pydub import AudioSegment
from io import BytesIO

from util.kafka.producer import KafkaProducerSingleton
import util.minio.client as minio
import util.audio.split as split
import util.db.client as db

router = APIRouter()


@router.post("")
def split_audio(id: str):
    producer = KafkaProducerSingleton.getInstance().producer

    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
                  "process": "CHUNKED", "status": "PROCESSING"})

    try:
        minio_client = minio.get_minio_client()
        data = minio_client.get_object(
            "input-audio",
            f"{id}.mp3",
        )
        content = data.read()
        chunks = split.split(AudioSegment.from_file(BytesIO(content)))
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "CHUNKED", "status": "FAILED"})
        return HTTPException(status_code="500", detail="Problem with retrieving item in MinIO bucket")

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

    for i, chunk in enumerate(chunks):
        output_buffer = BytesIO()
        chunk.export(output_buffer, format="mp3")
        output_buffer.seek(0)

        object_name = f"{id}-{i}.mp3"
        minio_client.put_object(
            bucket_name='audio-chunks',
            object_name=object_name,
            data=output_buffer,
            length=output_buffer.getbuffer().nbytes
        )

    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
                  "process": "CHUNKED", "status": "SUCCESS"})
