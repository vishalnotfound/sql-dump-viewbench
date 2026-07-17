import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = BASE_DIR / "sql"
STATIC_DIR = BASE_DIR / "frontend"

SQL_DIR.mkdir(exist_ok=True)
