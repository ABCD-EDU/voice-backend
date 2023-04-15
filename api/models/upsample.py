
from fastapi import APIRouter, HTTPException
import json

router = APIRouter()

# TODO: Add default values for paths
@router.post("/")
async def get_results(input_path: str, output_path: str):
    return "Upsample"