from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SQL_DIR
from services.file_service import FileService

router = APIRouter(prefix="/api/files/{filename}", tags=["tables"])
file_service = FileService(SQL_DIR)


@router.get("/tables")
async def list_tables(filename: str):
    """Get list of tables in a SQL file."""
    file_path = SQL_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        return file_service.get_tables(filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metadata")
async def get_metadata(filename: str):
    """Get metadata for a SQL file."""
    file_path = SQL_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        return file_service.get_metadata(filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table/{table_name}")
async def get_table_data(
    filename: str,
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    order: str = Query("asc"),
):
    """Get paginated data for a specific table."""
    file_path = SQL_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        data = file_service.get_table_data(
            filename=filename,
            table_name=table_name,
            page=page,
            page_size=page_size,
            search=search,
            sort=sort,
            order=order,
        )
        return data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
