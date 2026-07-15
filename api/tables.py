from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SQL_DIR, CACHE_DIR
from services.file_service import FileService
from services.table_service import TableService

router = APIRouter(prefix="/api/files", tags=["tables"])
file_service = FileService(SQL_DIR)
table_service = TableService(CACHE_DIR)


@router.get("/{filename}/tables")
async def list_tables(filename: str):
    file_path = file_service.get_sql_file_path(filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return table_service.get_tables(file_path)


@router.get("/{filename}/metadata")
async def get_metadata(filename: str):
    file_path = file_service.get_sql_file_path(filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return table_service.get_metadata(file_path)


@router.get("/{filename}/table/{table_name}")
async def get_table(
    filename: str,
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: str = Query(None),
    sort: str = Query(None),
    order: str = Query("asc"),
):
    file_path = file_service.get_sql_file_path(filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return table_service.get_table_data(
        file_path, table_name, page, page_size, search, sort, order
    )
