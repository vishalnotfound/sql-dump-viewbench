from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import SQL_DIR
from services.file_service import get_file_content, extract_tables, extract_table_data, _rows_to_dicts

router = APIRouter(prefix="/api/files/{filename}", tags=["tables"])


@router.get("/tables")
async def list_tables(filename: str):
    file_path = SQL_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    content = get_file_content(SQL_DIR, filename)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    table_names = extract_tables(content)
    return [{"name": name} for name in table_names]


@router.get("/table/{table_name}")
async def get_table_data(
    filename: str,
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    file_path = SQL_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    content = get_file_content(SQL_DIR, filename)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")

    columns, rows = extract_table_data(content, table_name)
    total_rows = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rows[start:end]
    page_rows = _rows_to_dicts(columns, page_rows)

    return {
        "table": table_name,
        "columns": [c["name"] for c in columns],
        "rows": page_rows,
        "total_rows": total_rows,
        "page": page,
        "total_pages": (total_rows + page_size - 1) // page_size,
    }


@router.get("/source")
async def get_source(filename: str):
    file_path = SQL_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    content = get_file_content(SQL_DIR, filename)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"tables": extract_tables(content)}
