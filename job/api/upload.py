from fastapi import APIRouter, UploadFile, File, HTTPException, Header, BackgroundTasks, Request
import uuid
from minio.error import S3Error
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import librosa
import soundfile as sf
import io
import base64
import requests

from util.audio.convert import convert_to_wav
import util.db.client as db
import util.minio.client as minio
from util.kafka.producer import KafkaProducerSingleton
import util.models.denoiser.denoise as denoise

router = APIRouter()

class Audio(BaseModel):
  denoise: bool
  audio: str


def upload_async(FILE_NAME, file, BUCKET_NAME, do_denoise):
    producer = KafkaProducerSingleton.getInstance().producer
    print(producer)
    producer.send('audio_processing_queue', key=FILE_NAME.encode("utf-8"), value={
                  "process": "UPLOAD", "status": "PROCESSING"})
    print("trest")

    try:
        if do_denoise:
          file = denoise.run(file)

        audio_bytes = io.BytesIO()
        sf.write(audio_bytes, file, 8000, format="wav")
        audio_bytes.seek(0)

        minio.get_minio_client().put_object(
            bucket_name=BUCKET_NAME,
            object_name=f"{FILE_NAME}.wav",
            data=audio_bytes,
            length=len(audio_bytes.getvalue()),
            content_type='audio/mpeg'
        )

        print("LOADED")
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

        print("UPDATED DB")
    except exc:
        producer.send('audio_processing_queue', key=FILE_NAME.encode("utf-8"), value={
                      "process": "UPLOAD", "status": "FAILED"})
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        """
        Triggers an Airflow DAG with the specified dag_id and configuration parameters in conf.
        """
        airflow_url = "http://localhost:8080/api/v1"
        dag_id = "audio_processing_dag_v3"
        dag_run_url = f"{airflow_url}/dags/{dag_id}/dagRuns"
        headers = {"Content-Type": "application/json", "Authorization": "Basic YWlyZmxvdzphaXJmbG93"}
        payload = {"conf": {
            "id": FILE_NAME
        }}

        print("TRIGGERED DAG")

        response = requests.post(dag_run_url, json=payload, headers=headers)
        response.raise_for_status()
    except:
        producer.send('audio_processing_queue', key=FILE_NAME.encode("utf-8"), value={
                      "process": "UPLOAD", "status": "FAILED"})
        raise HTTPException(status_code=500, detail=str(exc))


    producer.send('audio_processing_queue', key=FILE_NAME.encode("utf-8"), value={
        "process": "UPLOAD", "status": "SUCCESS"})

@router.post("", status_code=200)
async def upload(bg_tasks: BackgroundTasks, request: Request, audio: Audio):
    try:
        BUCKET_NAME = "input-audio"
        FILE_NAME = uuid.uuid4().hex

        audio_data = audio.audio
        do_denoise = audio.denoise
        # Convert base64-encoded audio data to bytes
        audio_bytes = io.BytesIO(base64.b64decode(audio_data.encode("utf-8")))
        print(audio_bytes)

        # Load audio data using librosa
        y, sr = librosa.load(audio_bytes, sr=8000)
        print("loaded")

        # Save audio data to disk
        sf.write("audio.wav", y, sr, format='WAV', subtype='PCM_16')

        # bg_tasks.add_task(upload_async, FILE_NAME, y, BUCKET_NAME, do_denoise)
        upload_async(FILE_NAME, y, BUCKET_NAME, do_denoise)

        return JSONResponse(content={"generated_id": FILE_NAME})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)