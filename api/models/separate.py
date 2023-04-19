from fastapi import APIRouter, HTTPException
from io import BytesIO
from pydub import AudioSegment

import util.models.speech_separation.main as separate
from util.db.client import get_db
from util.kafka.producer import KafkaProducerSingleton
from util.minio.client import get_minio_client

router = APIRouter()


@router.get("/", status_code=201)
async def get_results(id: str):
    producer = KafkaProducerSingleton.getInstance().producer
    minio = get_minio_client()

    # TODO: Kafka Producer Events
    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
        "process": "SEPARATION", "status": "PROCESSING"})

    # try:
    object_data = minio.get_object(
        "input-audio",
        f"{id}.mp3"
    )
    object_content = object_data.read()
    audio_data = BytesIO(object_content)
    print(audio_data)
    audio_outputs = separate.run(audio_bytes=audio_data)
    print("sep don")

    # TODO: Bucket writes
    print("OUTPUTS", audio_outputs)
    for speaker in range(len(audio_outputs)):
        audio_outputs[speaker].seek(0)
        audio_test = AudioSegment.from_file(audio_outputs[speaker])
        output_test = BytesIO()
        audio_test.export(output_test, format="mp3", bitrate="8k")
        output_test.seek(0)

        print("SPEAKER:", audio_outputs[speaker], "LENGTH:", len(
            audio_outputs[speaker].getvalue()), "INDEX:", speaker+1)
        minio.put_object(
            bucket_name='separated-audio',
            object_name=f"{id}-{speaker + 1}.mp3",
            data=output_test,
            length=len(output_test.getvalue())
        )
    # except:
    #     producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
    #         "process": "SEPARATION", "status": "FAILED"})
    #     return HTTPException(status_code="500", detail="Problem with retrieving item in MinIO bucket")

    # TODO: DB Update writes
    try:
        cursor = get_db().cursor()
        query = """
          UPDATE requests
          SET status = 'SEPARATED'
          WHERE filename = %s;
        """
        values = (id)

        cursor.execute(query, values)
        get_db().commit()
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "SEPARATION", "status": "FAILED"})
        return HTTPException(status_code="500", detail="Problem with retrieving item in MySQL")

    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
        "process": "SEPARATION", "status": "SUCCESS"})
