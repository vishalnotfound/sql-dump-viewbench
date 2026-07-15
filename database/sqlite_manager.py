import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.models import Table, ParsedSQL


class SQLiteManager:
    def __init__(self, sql_file_path: Path, cache_dir: Path):
        self.sql_file_path = sql_file_path
        self.cache_file = cache_dir / f"{sql_file_path.name}.sqlite"
        self.conn: Optional[sqlite3.Connection] = None

    def get_file_hash(self) -> str:
        hash_obj = hashlib.sha256()
        with open(self.sql_file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def is_cache_valid(self) -> bool:
        if not self.cache_file.exists():
            return False
        try:
            conn = sqlite3.connect(self.cache_file)
            cursor = conn.cursor()
            # Check if metadata table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'")
            if not cursor.fetchone():
                conn.close()
                return False
            cursor.execute("SELECT file_hash FROM metadata")
            cached_hash = cursor.fetchone()
            conn.close()
            return cached_hash and cached_hash[0] == self.get_file_hash()
        except Exception:
            return False

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.cache_file)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_cache(self, parsed: ParsedSQL):
        self.close()
        if self.cache_file.exists():
            self.cache_file.unlink()
        conn = self.connect()
        cursor = conn.cursor()
        # Create metadata table
        cursor.execute(
            """
            CREATE TABLE metadata (
                id INTEGER PRIMARY KEY,
                file_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("INSERT INTO metadata (file_hash) VALUES (?)", (self.get_file_hash(),))
        # Create tables for each SQL table
        for table_name, table in parsed.tables.items():
            # Sanitize table name for SQLite
            safe_table_name = table_name.replace(" ", "_").replace("-", "_")
            # Create columns
            col_defs = []
            for col in table.columns:
                safe_col_name = col.name.replace(" ", "_").replace("-", "_")
                col_defs.append(f'"{safe_col_name}" TEXT')
            create_sql = f'CREATE TABLE "{safe_table_name}" ({", ".join(col_defs)})'
            cursor.execute(create_sql)
            # Insert rows in batches
            if table.rows:
                placeholders = ", ".join(["?"] * len(table.columns))
                insert_sql = f'INSERT INTO "{safe_table_name}" VALUES ({placeholders})'
                batch_size = 1000
                for i in range(0, len(table.rows), batch_size):
                    batch = table.rows[i : i + batch_size]
                    cursor.executemany(insert_sql, batch)
        conn.commit()
        self.close()

    def get_tables(self) -> List[Dict[str, Any]]:
        conn = self.connect()
        cursor = conn.cursor()
        # Get all tables except metadata
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'metadata' ORDER BY name"
        )
        tables = []
        for row in cursor.fetchall():
            table_name = row["name"]
            # Get row count
            cursor.execute(f'SELECT COUNT(*) as count FROM "{table_name}"')
            count = cursor.fetchone()["count"]
            tables.append({"name": table_name, "rows": count})
        self.close()
        return tables

    def get_table_data(
        self,
        table_name: str,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        order: str = "asc",
    ) -> Dict[str, Any]:
        conn = self.connect()
        cursor = conn.cursor()
        # Get columns
        cursor.execute(f'PRAGMA table_info("{table_name}")')
        columns = [row["name"] for row in cursor.fetchall()]
        # Build query
        where_clause = ""
        params = []
        if search:
            search_terms = [f'"{col}" LIKE ?' for col in columns]
            where_clause = " WHERE " + " OR ".join(search_terms)
            params = [f"%{search}%"] * len(columns)
        # Count total
        count_sql = f'SELECT COUNT(*) as count FROM "{table_name}"{where_clause}'
        cursor.execute(count_sql, params)
        total = cursor.fetchone()["count"]
        # Sort
        order_clause = ""
        if sort and sort in columns:
            safe_order = "ASC" if order.lower() == "asc" else "DESC"
            order_clause = f' ORDER BY "{sort}" {safe_order}'
        # Pagination
        offset = (page - 1) * page_size
        data_sql = f'SELECT * FROM "{table_name}"{where_clause}{order_clause} LIMIT ? OFFSET ?'
        cursor.execute(data_sql, params + [page_size, offset])
        rows = []
        for row in cursor.fetchall():
            rows.append(dict(row))
        self.close()
        return {
            "columns": columns,
            "rows": rows,
            "row_count": total,
        }

    def get_metadata(self) -> Dict[str, Any]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM metadata")
        metadata = dict(cursor.fetchone())
        # Get file stats
        stat = self.sql_file_path.stat()
        metadata["file_size"] = stat.st_size
        # Get total tables
        cursor.execute(
            "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table' AND name != 'metadata'"
        )
        metadata["num_tables"] = cursor.fetchone()["count"]
        # Get total rows
        total_rows = 0
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'metadata'"
        )
        for row in cursor.fetchall():
            table_name = row["name"]
            cursor.execute(f'SELECT COUNT(*) as count FROM "{table_name}"')
            total_rows += cursor.fetchone()["count"]
        metadata["total_rows"] = total_rows
        self.close()
        return metadata
