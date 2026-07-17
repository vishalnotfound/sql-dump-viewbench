import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from fastapi import UploadFile
import hashlib
import time


class SQLParser:
    """Parses SQL dump files to extract table schemas and data."""

    def __init__(self):
        self.current_table = None
        self.tables: Dict[str, Dict[str, Any]] = {}
        self.columns: List[str] = []
        self.column_types: Dict[str, str] = {}

    def parse(self, sql_content: str) -> Dict[str, Any]:
        """Parse SQL dump content and return structured data."""
        self.tables = {}
        self.current_table = None
        self.columns = []
        self.column_types = {}

        # Normalize line endings
        sql_content = sql_content.replace("\r\n", "\n")

        lines = sql_content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip comments and empty lines
            if not line or line.startswith("--") or line.startswith("#"):
                i += 1
                continue

            # Detect CREATE TABLE statement
            if line.upper().startswith("CREATE TABLE"):
                create_lines = [line]
                i += 1
                depth = 1
                while i < len(lines) and depth > 0:
                    stripped = lines[i].strip()
                    create_lines.append(stripped)
                    for ch in stripped:
                        if ch == "(":
                            depth += 1
                        elif ch == ")":
                            depth -= 1
                    if depth == 0:
                        break
                    i += 1
                i += 1

                self._parse_create_table("\n".join(create_lines))
                continue

            # Detect INSERT INTO statement
            if line.upper().startswith("INSERT INTO"):
                insert_lines = [line]
                i += 1
                while i < len(lines):
                    stripped = lines[i].strip()
                    insert_lines.append(stripped)
                    if stripped.endswith(";"):
                        i += 1
                        break
                    i += 1

                self._parse_insert_into("\n".join(insert_lines))
                continue

            i += 1

        return {
            "tables": {
                name: {
                    "name": table["name"],
                    "columns": table["columns"],
                    "rows": table["rows"],
                    "row_count": len(table["rows"]),
                }
                for name, table in self.tables.items()
            },
            "num_tables": len(self.tables),
            "total_rows": sum(len(t["rows"]) for t in self.tables.values()),
        }

    def _parse_create_table(self, sql: str):
        """Parse CREATE TABLE statement."""
        # Extract table name
        match = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?(\w+)[`\"']?", sql, re.IGNORECASE)
        if not match:
            return
        table_name = match.group(1)

        # Extract column definitions - find the content between the first ( and last )
        paren_start = sql.index("(")
        paren_end = sql.rindex(")")
        cols_section = sql[paren_start + 1:paren_end]

        columns = []
        column_types = {}

        # Split by commas, but be careful of commas inside nested parentheses (like in DEFAULT clauses)
        parts = self._split_columns(cols_section)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Skip constraints like PRIMARY KEY, INDEX, KEY, UNIQUE, CONSTRAINT, FOREIGN KEY
            if any(
                part.upper().startswith(keyword)
                for keyword in [
                    "PRIMARY KEY",
                    "INDEX",
                    "KEY",
                    "UNIQUE",
                    "CONSTRAINT",
                    "FOREIGN KEY",
                    "FULLTEXT",
                    "SPATIAL",
                    "CHECK",
                ]
            ):
                continue

            # Parse column definition
            col_match = re.match(
                r"[`\"']?(\w+)[`\"']?\s+(\w+(?:\s*\([^)]*\))?)\s*(.*)",
                part,
                re.IGNORECASE,
            )
            if col_match:
                col_name = col_match.group(1)
                col_type = col_match.group(2).strip().upper()
                col_options = col_match.group(3).strip().upper()

                # Determine nullable
                nullable = "NOT NULL" not in col_options

                # Determine default
                default = None
                default_match = re.search(
                    r"DEFAULT\s+('(?:[^']|'')*'|[^\s,)]+)", col_options
                )
                if default_match:
                    default = default_match.group(1)
                    # Strip quotes from string defaults
                    if default.startswith("'") and default.endswith("'"):
                        default = default[1:-1]

                # Determine primary key
                primary_key = "PRIMARY KEY" in col_options or "AUTO_INCREMENT" in col_options

                columns.append(
                    {
                        "name": col_name,
                        "type": col_type,
                        "nullable": nullable,
                        "default": default,
                        "primary_key": primary_key,
                    }
                )
                column_types[col_name] = col_type

        self.tables[table_name] = {
            "name": table_name,
            "columns": columns,
            "rows": [],
            "row_count": 0,
        }
        self.column_types = column_types

    def _split_columns(self, cols_section: str) -> List[str]:
        """Split column definitions by commas, respecting nested parentheses."""
        parts = []
        depth = 0
        current = []
        i = 0
        while i < len(cols_section):
            ch = cols_section[i]
            if ch == "(":
                depth += 1
                current.append(ch)
            elif ch == ")":
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(ch)
            i += 1
        if current:
            parts.append("".join(current))
        return parts

    def _parse_insert_into(self, sql: str):
        """Parse INSERT INTO statement."""
        # Extract table name
        match = re.search(
            r"INSERT\s+INTO\s+[`\"']?(\w+)[`\"']?(?:\s*\(([^)]+)\))?\s*VALUES",
            sql,
            re.IGNORECASE,
        )
        if not match:
            return
        table_name = match.group(1)

        if table_name not in self.tables:
            # Table wasn't defined via CREATE TABLE - create a minimal schema
            self.tables[table_name] = {
                "name": table_name,
                "columns": [],
                "rows": [],
                "row_count": 0,
            }

        # Parse the column names if specified
        insert_columns = None
        if match.group(2):
            insert_columns = [
                c.strip().strip("`\"'") for c in match.group(2).split(",")
            ]

        # Find the VALUES part
        values_start = sql.upper().rfind("VALUES")
        if values_start == -1:
            return
        values_part = sql[values_start + len("VALUES"):].strip()

        # Parse rows - handle multiple value rows like (1,'a'),(2,'b')
        rows = self._parse_values(values_part)

        # Determine columns for this table
        if insert_columns:
            columns = insert_columns
        else:
            # Use columns from CREATE TABLE if available
            existing_cols = [c["name"] for c in self.tables[table_name].get("columns", [])]
            if existing_cols:
                columns = existing_cols
            else:
                # Infer from number of values
                if rows:
                    columns = [f"col{i + 1}" for i in range(len(rows[0]))]
                    self.tables[table_name]["columns"] = [
                        {"name": c, "type": "VARCHAR", "nullable": True}
                        for c in columns
                    ]

        # Convert rows to dicts
        for row_values in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                if i < len(row_values):
                    row_dict[col] = row_values[i]
                else:
                    row_dict[col] = None
            self.tables[table_name]["rows"].append(row_dict)

        self.tables[table_name]["row_count"] = len(
            self.tables[table_name]["rows"]
        )

    def _parse_values(self, values_str: str) -> List[List[Any]]:
        """Parse value tuples from INSERT statement."""
        rows = []
        i = 0
        while i < len(values_str):
            if values_str[i] == "(":
                # Find matching closing paren
                depth = 1
                j = i + 1
                while j < len(values_str) and depth > 0:
                    if values_str[j] == "(":
                        depth += 1
                    elif values_str[j] == ")":
                        depth -= 1
                    j += 1

                row_str = values_str[i + 1:j - 1]
                row_values = self._parse_row_values(row_str)
                rows.append(row_values)
                i = j
            else:
                i += 1
        return rows

    def _parse_row_values(self, row_str: str) -> List[Any]:
        """Parse individual values from a row tuple."""
        values = []
        i = 0
        while i < len(row_str):
            # Skip whitespace and commas
            if row_str[i] in " ,":
                i += 1
                continue

            # Handle NULL
            if row_str[i:].upper().startswith("NULL"):
                values.append(None)
                i += 4
                continue

            # Handle quoted string
            if row_str[i] == "'":
                j = i + 1
                while j < len(row_str):
                    if row_str[j] == "'":
                        # Check for escaped quote ''
                        if j + 1 < len(row_str) and row_str[j + 1] == "'":
                            j += 2
                            continue
                        break
                    j += 1
                val = row_str[i + 1:j]
                # Unescape double quotes
                val = val.replace("''", "'")
                values.append(val)
                i = j + 1
                continue

            # Handle number or other value
            j = i
            while j < len(row_str) and row_str[j] not in ",)":
                j += 1
                if j < len(row_str) and row_str[j] == "'" and row_str[j-1] != "\\":
                    break
            val = row_str[i:j].strip()
            # Try to convert to number
            try:
                if "." in val:
                    val = float(val)
                else:
                    val = int(val)
            except (ValueError, TypeError):
                pass
            values.append(val)
            i = j

        return values


class MetadataService:
    """Handles metadata for SQL files."""

    METADATA_FILE = "metadata.json"

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = cache_dir / self.METADATA_FILE
        self._metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from cache file."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_metadata(self):
        """Save metadata to cache file."""
        with open(self.metadata_path, "w") as f:
            json.dump(self._metadata, f, indent=2)

    def get_metadata(self, filename: str, file_path: Path) -> Dict[str, Any]:
        """Get metadata for a file, computing if necessary."""
        # Check if cached and file hasn't changed
        file_stat = file_path.stat()
        last_modified = file_stat.st_mtime
        file_size = file_stat.st_size

        if filename in self._metadata:
            cached = self._metadata[filename]
            if cached.get("last_modified") == last_modified and cached.get("file_size") == file_size:
                return cached

        # Compute fresh metadata
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        parser = SQLParser()
        result = parser.parse(content)

        metadata = {
            "filename": filename,
            "file_size": file_size,
            "last_modified": last_modified,
            "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "num_tables": result["num_tables"],
            "total_rows": result["total_rows"],
            "tables": list(result["tables"].keys()),
        }

        self._metadata[filename] = metadata
        self._save_metadata()

        return metadata

    def invalidate(self, filename: str):
        """Invalidate cached metadata for a file."""
        if filename in self._metadata:
            del self._metadata[filename]
            self._save_metadata()


class FileService:
    """Service for managing SQL files and parsing them."""

    def __init__(self, sql_dir: Path):
        self.sql_dir = sql_dir
        self.sql_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = sql_dir.parent / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_service = MetadataService(self.cache_dir)
        self._table_cache: Dict[str, Dict[str, Any]] = {}

    def get_sql_files(self) -> List[Dict[str, Any]]:
        """List all SQL files in the directory."""
        files = []
        for f in sorted(self.sql_dir.glob("*.sql")):
            stat = f.stat()
            files.append(
                {
                    "name": f.name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )
        return files

    async def save_uploaded_file(self, file: UploadFile) -> Dict[str, Any]:
        """Save an uploaded SQL file."""
        file_path = self.sql_dir / file.filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        stat = file_path.stat()
        return {
            "name": file.filename,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        }

    def delete_file(self, filename: str) -> bool:
        """Delete a SQL file."""
        file_path = self.sql_dir / filename
        if not file_path.exists():
            return False

        file_path.unlink()
        self.metadata_service.invalidate(filename)
        # Clear table cache for this file
        self._table_cache.pop(filename, None)
        return True

    def parse_file(self, filename: str) -> Dict[str, Any]:
        """Parse a SQL file and return structured data."""
        file_path = self.sql_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File {filename} not found")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        parser = SQLParser()
        result = parser.parse(content)

        # Cache tables
        self._table_cache[filename] = result["tables"]

        return result

    def get_tables(self, filename: str) -> List[Dict[str, Any]]:
        """Get list of tables in a SQL file."""
        result = self.parse_file(filename)
        tables = []
        for table_name, table_data in result["tables"].items():
            tables.append(
                {
                    "name": table_name,
                    "columns": table_data["columns"],
                    "rows": table_data["row_count"],
                }
            )
        return tables

    def get_table_data(
        self,
        filename: str,
        table_name: str,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        order: str = "asc",
    ) -> Dict[str, Any]:
        """Get paginated data for a specific table."""
        # Parse file if not cached
        if filename not in self._table_cache:
            self.parse_file(filename)

        tables = self._table_cache.get(filename, {})
        table = tables.get(table_name)
        if not table:
            raise FileNotFoundError(f"Table {table_name} not found in {filename}")

        columns = [c["name"] for c in table["columns"]]
        rows = list(table["rows"])

        # Apply search filter
        if search:
            search_lower = search.lower()
            filtered_rows = []
            for row in rows:
                for col in columns:
                    val = str(row.get(col, "")).lower()
                    if search_lower in val:
                        filtered_rows.append(row)
                        break
            rows = filtered_rows

        # Apply sorting
        if sort and sort in columns:
            reverse = order == "desc"
            try:
                rows.sort(key=lambda r: (r.get(sort) is not None, r.get(sort) or ""), reverse=reverse)
            except TypeError:
                rows.sort(key=lambda r: str(r.get(sort, "")), reverse=reverse)

        # Apply pagination
        total_rows = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_rows = rows[start:end]

        return {
            "columns": columns,
            "rows": paginated_rows,
            "row_count": total_rows,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_rows + page_size - 1) // page_size,
        }

    def get_metadata(self, filename: str) -> Dict[str, Any]:
        """Get metadata for a SQL file."""
        file_path = self.sql_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File {filename} not found")
        return self.metadata_service.get_metadata(filename, file_path)