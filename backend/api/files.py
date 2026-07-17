from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SQL_DIR
from services.file_service import FileService

router = APIRouter(prefix="/api/files", tags=["files"])
file_service = FileService(SQL_DIR)


@router.get("")
async def list_files():
    return file_service.get_sql_files()


@router.get("/{filename}/source", response_class=PlainTextResponse)
async def get_source(filename: str):
    """Return raw SQL source for a file."""
    file_path = SQL_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".sql"):
        raise HTTPException(status_code=400, detail="Only SQL files are allowed")
    try:
        saved_file = await file_service.save_uploaded_file(file)
        return {"success": True, "file": saved_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{filename}")
async def delete_file(filename: str):
    success = file_service.delete_file(filename)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"success": True, "message": "File deleted"}
