
from fastapi import APIRouter, HTTPException
import json

import util.separate_model as separate

router = APIRouter()

# TODO: Add default values for paths
@router.get("/")
async def get_results(input_path: str, output_path: str):
    separate.load_and_run(input_path, output_path)
    return True