from fastapi import APIRouter, HTTPException
import minio

import util.minio.client as minio
from util.db.client import get_db

router = APIRouter()

def get_files(audio_id: str, bucket: str):
  speakers = []
  for i in range(2):
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
    "separated": [],
    "upsampled": []
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
    print(rows)
    curr_status = rows[0]
  except:
    raise HTTPException(status_code=500, detail="Problem with retrieving item in MySQL")

  # TODO: DECIDE IF RETRIEVING SEPARATED ONLY OR BOTH SEPARATED AND UPSAMPLED
  try:
    if curr_status == "SEPARATED":
       audio_files["separated"] = get_files(audio_id=audio_id, bucket="separated-recompiled-audio")
    elif curr_status == "COMPLETED":
       audio_files["separated"] = get_files(audio_id=audio_id, bucket="separated-recompiled-audio")
       audio_files["upsampled"] = get_files(audio_id=audio_id, bucket="upsampled-recompiled-audio")
  except:
     raise HTTPException(status_code=500, detail="Problem with retrieving item in MinIO")

  print(audio_files)

  return audio_files