from fastapi import APIRouter, HTTPException
from io import BytesIO

import util.audio.compile as cp
import util.models.speaker_id.main as identify
from util.db.client import get_db
from util.kafka.producer import KafkaProducerSingleton
from util.minio.client import get_minio_client

router = APIRouter()


@router.post("/", status_code=201)
def run(id: str):
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
            "process": "UPSAMPLING", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with retrieving item in MySQL")

    upsampled_audios = []
    try:
        print("GETTING ITEMS FROM BUCKET")
        # TODO: Get chunks from MinIO bucket (audio-chunks)
        for chunk in range(num_chunks):
            chunk_index = chunk + 1
            for i in range(2):
                print("RETRIEVING", f"{id}-{chunk_index}-{i+1}.wav")

                object_data = minio.get_object(
                    bucket_name="separated-audio",
                    object_name=f"{id}-{chunk_index}-{i+1}.wav",
                )
                object_content = object_data.read()
                audio_bytes = BytesIO(object_content)
                upsampled_audios.append(audio_bytes)
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with retrieving item in MinIO")

    audio_idx = 0
    for chunk in range(num_chunks):
        chunk_index = chunk + 1

        audio1 = upsampled_audios[audio_idx]
        audio2 = upsampled_audios[audio_idx+1]
        print("RETRIEVED INDEX", audio_idx, audio_idx+1)
        print(audio1, audio2)

        print("COMPILING...")
        compiled_audio = cp.compile(audio1, audio2)
        compiled_audio.seek(0)
        print(compiled_audio)
        print("COMPILED")
        buffer_list = identify.run(compiled_audio)
        print("IDENTIFIED")
        print("seeeking")
        buffer_list[0].seek(0)
        buffer_list[1].seek(0)
        print("seeked")

        for audio in range(len(buffer_list)):
            # TODO: Write Output to MinIO bucket (upsampled-audio)
            minio.put_object(
                bucket_name="identified-audio",
                object_name=f"{id}-{chunk_index}-{audio+1}.wav",
                data=buffer_list[audio],
                length=len(buffer_list[audio].getvalue())
            )
        audio_idx += 2
