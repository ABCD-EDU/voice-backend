from fastapi import APIRouter, UploadFile, File, HTTPException, Header, BackgroundTasks
import uuid
from minio.error import S3Error

from util.audio.convert import convert_to_wav
import util.db.client as db
import util.minio.client as minio
from util.kafka.producer import KafkaProducerSingleton

router = APIRouter()

async def upload_async(FILE_NAME, file, BUCKET_NAME, content_length):
    producer = KafkaProducerSingleton.getInstance().producer
    producer.send('audio_processing_queue', key=FILE_NAME.encode("utf-8"), value={
                  "process": "UPLOAD", "status": "PROCESSING"})

    FILE_FORMAT = file.filename.split(".")[-1]

    if FILE_FORMAT != "wav":
        audio_content = await file.read()
        wav_buffer = convert_to_wav(audio_content)

    try:
        minio.get_minio_client().put_object(
            bucket_name=BUCKET_NAME,
            object_name=f"{FILE_NAME}.wav",
            data=wav_buffer if FILE_FORMAT != "wav" else file.file,
            length=wav_buffer.getbuffer().nbytes if FILE_FORMAT != 'wav' else int(content_length)-500,
            content_type='audio/mpeg'
        )
    except S3Error as exc:
        producer.send('audio_processing_queue', key=FILE_NAME.encode("utf-8"), value={
                      "process": "UPLOAD", "status": "FAILED"})
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        query = """
          INSERT INTO requests (filename, num_chunks, status)
          VALUES (%s, %s, %s);
        """
        values = (FILE_NAME, 0, "PENDING")

        cursor = db.get_db().cursor()
        cursor.execute(query, values)
        db.get_db().commit()
    except exc:
        producer.send('audio_processing_queue', key=FILE_NAME.encode("utf-8"), value={
                      "process": "UPLOAD", "status": "FAILED"})
        raise HTTPException(status_code=500, detail=str(exc))

    producer.send('audio_processing_queue', key=FILE_NAME.encode("utf-8"), value={
        "process": "UPLOAD", "status": "SUCCESS"})

@router.post("", status_code=200)
async def upload_audio_file(
    bg_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    content_length: str = Header(...)
):
    BUCKET_NAME = "input-audio"
    FILE_NAME = uuid.uuid4().hex

    bg_tasks.add_task(upload_async, FILE_NAME, file, BUCKET_NAME, content_length)

    return FILE_NAME
