
from fastapi import APIRouter, HTTPException
import json
from io import BytesIO

from util.db.client import get_db
from util.minio.client import get_minio_client
from util.models.audio_upsample.main import run as upsample
from util.kafka.producer import KafkaProducerSingleton

router = APIRouter()


@router.post("/")
async def get_results(id: str):
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

        rows = cursor.fetchone()
        num_chunks = rows[0]
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        return HTTPException(status_code="500", detail="Problem with retrieving item in MySQL")

    separated_audios = []
    try:
        print("GETTING ITEMS FROM BUCKET")
        # TODO: Get chunks from MinIO bucket (audio-chunks)
        for chunk in range(num_chunks):
            for i in range(2):
                print("RETRIEVING", id, i+1)
                object_data = minio.get_object(
                    bucket_name="separated-audio",
                    object_name=f"{id}-{chunk}-{i+1}.mp3",
                )
                object_content = object_data.read()
                audio_bytes = BytesIO(object_content)
                separated_audios.append(audio_bytes)
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        return HTTPException(status_code="500", detail="Problem with retrieving item in MinIO")

    # TODO: Call upsample.run()
    try:
        print("STARTING UPSAMPLE")
        print(len(separated_audios))
        for chunk in range(num_chunks):
            for audio in range(len(separated_audios)):
                print("CURRENT:", audio)
                curr_audio = separated_audios[audio]
                audio_buffer = upsample(curr_audio)
                audio_buffer.seek(0)

                # TODO: Write Output to MinIO bucket (upsampled-audio)
                minio.put_object(
                    bucket_name="upsampled-audio",
                    object_name=f"{id}-{chunk}-{audio+1}.wav",
                    data=audio_buffer,
                    length=len(audio_buffer.getvalue())
                )
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        return HTTPException(status_code="500", detail="Problem with putting item in MinIO")

    # TODO: Write DB Status Update
    try:
        print("UPDATING STATUS FROM DB")
        cursor = get_db().cursor()
        query = """
          UPDATE requests
          SET status = 'UPSAMPLED'
          WHERE filename = %s;
        """
        values = (id)

        cursor.execute(query, values)
        get_db().commit()
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        return HTTPException(status_code="500", detail="Problem with updating item in MySQL")

    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
        "process": "UPSAMPLING", "status": "SUCCESS"})

    return id
