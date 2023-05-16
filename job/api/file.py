from fastapi import APIRouter, HTTPException
import minio

import util.minio.client as minio
from util.db.client import get_db

router = APIRouter()

statuses = {
  "TWO_SPEAKERS_COMPLETED": 1,
  "THREE_SPEAKERS_SEPARATED": 2,
  "THREE_SPEAKERS_RELABEL": 3,
  "THREE_SPEAKERS_UPSAMPLED": 4,
  "THREE_SPEAKERS_COMPLETED": 5,
}

def get_files(audio_id: str, bucket: str, speaker_count: int):
  speakers = []
  for i in range(speaker_count):
    audio_url = minio.get_minio_client().presigned_get_object(
      bucket, f"{audio_id}-{i+1}.wav",
    )
    speakers.append(audio_url)
  return speakers

@router.get("/separated/{audio_id}")
async def get_sep_file(audio_id: str):
  speakers = get_files(audio_id, "separated-recompiled-audio")
  print(speakers)
  return { "audio_url": speakers}

@router.get("/upsampled/{audio_id}")
async def get_sep_file(audio_id: str):
  speakers = get_files(audio_id, "upsampled-recompiled-audio")
  print(speakers)
  return { "audio_url": speakers }

@router.get("/all/{audio_id}")
async def get_all(audio_id: str):
  audio_files = {
    "original": "",
    "separated": {
      "two_speakers": [],
      "three_speakers": []
    },
    "upsampled": {
      "two_speakers": [],
      "three_speakers": []
    }
  }
  # TODO: RETRIEVE STATUS FROM DB
  try:
    cursor = get_db().cursor()
    query = "SELECT status FROM requests WHERE filename = %s LIMIT 1;"
    values = (audio_id,)
    print(values)

    cursor.execute(query, values)
    get_db().commit()
    print("queries")

    rows = cursor.fetchone()
    print("ROWS", rows)
    curr_status = rows[0]
  except:
      raise HTTPException(status_code=500, detail="Problem with retrieving item in MySQL")

  # TODO: DECIDE IF RETRIEVING SEPARATED ONLY OR BOTH SEPARATED AND UPSAMPLED
  try:
    audio_files["original"] = minio.get_minio_client().presigned_get_object(
      "input-audio", f"{audio_id}.wav"
    )
    if statuses[curr_status] < statuses["THREE_SPEAKERS_COMPLETED"]:
      audio_files["separated"]["two_speakers"] = get_files(audio_id=audio_id, bucket="separated-recompiled-audio", speaker_count=2)
      audio_files["upsampled"]["two_speakers"] = get_files(audio_id=audio_id, bucket="upsampled-recompiled-audio", speaker_count=2)
    if curr_status == "THREE_SPEAKERS_COMPLETED":
      audio_files["separated"]["two_speakers"] = get_files(audio_id=audio_id, bucket="separated-recompiled-audio", speaker_count=2)
      audio_files["upsampled"]["two_speakers"] = get_files(audio_id=audio_id, bucket="upsampled-recompiled-audio", speaker_count=2)
      audio_files["separated"]["three_speakers"] = get_files(audio_id=audio_id, bucket="3-speaker-recompiled-separated-audio", speaker_count=3)
      audio_files["upsampled"]["three_speakers"] = get_files(audio_id=audio_id, bucket="3-speaker-recompiled-upsampled-audio", speaker_count=3)

  except:
     raise HTTPException(status_code=500, detail="Problem with retrieving item in MinIO")

  print(curr_status, audio_files)

  return audio_files
