from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import SQL_DIR
from services.file_service import get_sql_files, save_uploaded_file, delete_file

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("")
async def list_files():
    return get_sql_files(SQL_DIR)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".sql"):
        raise HTTPException(status_code=400, detail="Only SQL files allowed")
    try:
        return await save_uploaded_file(SQL_DIR, file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{filename}")
async def delete_file(filename: str):
    if not delete_file(SQL_DIR, filename):
        raise HTTPException(status_code=404, detail="File not found")
    return {"success": True}
