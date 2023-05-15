
from fastapi import APIRouter, HTTPException
from io import BytesIO

from util.db.client import get_db
from util.minio.client import get_minio_client
from util.models.audio_upsample.main import run as upsample
from util.kafka.producer import KafkaProducerSingleton

router = APIRouter()


@router.post("/", status_code=201)
async def get_results(id: str, speaker_count: int):
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

        rows = cursor.fetchone()
        num_chunks = rows[0]
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with retrieving item in MySQL")

    print("NUM OF CHNKS", num_chunks)
    separated_audios = []
    try:
        print("GETTING ITEMS FROM BUCKET")
        # TODO: Get chunks from MinIO bucket (audio-chunks)
        for chunk in range(num_chunks):
            chunk_index = chunk + 1
            for i in range(speaker_count):
                print("RETRIEVING", f"{id}-{chunk_index}-{i+1}.wav from", "separated-audio" if speaker_count == 2 else "3-speaker-separated-audio")

                object_data = minio.get_object(
                    bucket_name="separated-audio" if speaker_count == 2 else "3-speaker-separated-audio" ,
                    object_name=f"{id}-{chunk_index}-{i+1}.wav",
                )
                object_content = object_data.read()
                audio_bytes = BytesIO(object_content)
                separated_audios.append(audio_bytes)
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with retrieving item in MinIO")

    # TODO: Call upsample.run()
    try:
      print("STARTING UPSAMPLE")
      print(len(separated_audios))

      sep_audio = 0
      for chunk in range(num_chunks):
          chunk_index = chunk + 1
          for speaker in range(speaker_count):
              print("CURRENT:", "CHUNK", chunk_index, "SPEAKER",
                    speaker+1, "SEP_AUDIO", sep_audio)
              curr_audio = separated_audios[sep_audio]
              print(curr_audio)
              audio_buffer = upsample(curr_audio)
              print("seeeking")
              audio_buffer.seek(0)
              print("seeked")

              # TODO: Write Output to MinIO bucket (upsampled-audio)
              minio.put_object(
                  bucket_name="upsampled-audio" if speaker_count == 2 else "3-speaker-upsampled-audio",
                  object_name=f"{id}-{chunk_index}-{speaker+1}.wav",
                  data=audio_buffer,
                  length=len(audio_buffer.getvalue())
              )
              sep_audio += 1
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        raise HTTPException(
            status_code=500, detail="Problem with putting item in MinIO")

    # TODO: Write DB Status Update
    try:
        print("UPDATING STATUS FROM DB")
        cursor = get_db().cursor()
        query = """
          UPDATE requests
          SET status = 'UPSAMPLED'
          WHERE filename = %s;
        """
        values = (id,)

        cursor.execute(query, values)
        get_db().commit()
    except:
        producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
            "process": "UPSAMPLING", "status": "FAILED"})
        return HTTPException(status_code=500, detail="Problem with updating item in MySQL")

    producer.send('audio_processing_queue', key=id.encode("utf-8"), value={
        "process": "UPSAMPLING", "status": "SUCCESS"})

    return id
