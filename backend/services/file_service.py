from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
import re


def get_sql_files(sql_dir: Path):
    files = []
    for f in sorted(sql_dir.glob("*.sql")):
        stat = f.stat()
        files.append({
            "name": f.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return files


async def save_uploaded_file(sql_dir: Path, file: UploadFile):
    file_path = sql_dir / file.filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    stat = file_path.stat()
    return {
        "name": file.filename,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


def delete_file(sql_dir: Path, filename: str):
    file_path = sql_dir / filename
    if not file_path.exists():
        return False
    file_path.unlink()
    return True


def get_file_content(sql_dir: Path, filename: str):
    file_path = sql_dir / filename
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_tables(sql_content: str):
    tables = []
    for match in re.finditer(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?(\w+)[`\"']?\s*\(", sql_content, re.IGNORECASE):
        tables.append(match.group(1))
    return tables


def extract_schema(sql_content: str):
    schema = []
    for match in re.finditer(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?(\w+)[`\"']?\s*\(", sql_content, re.IGNORECASE):
        table_name = match.group(1)
        start = match.end()
        depth = 1
        i = start
        while i < len(sql_content) and depth > 0:
            ch = sql_content[i]
            if ch == '(': depth += 1
            elif ch == ')': depth -= 1
            i += 1
        
        cols_section = sql_content[start:i-1]
        
        pks = []
        fks = []
        for col_match in re.finditer(r"[`\"']?(\w+)[`\"']?\s+[^,]*?PRIMARY\s+KEY", cols_section, re.IGNORECASE):
            col_name = col_match.group(1)
            if col_name.upper() not in ("PRIMARY", "KEY", "INDEX", "UNIQUE", "CONSTRAINT", "FOREIGN", "CHECK"):
                pks.append(col_name)
                
        pk_match = re.search(r"PRIMARY\s+KEY\s*\(([^)]+)\)", cols_section, re.IGNORECASE)
        if pk_match:
            pk_cols = re.findall(r"[`\"']?(\w+)[`\"']?", pk_match.group(1))
            for c in pk_cols:
                if c not in pks:
                    pks.append(c)
                    
        for fk_match in re.finditer(r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+[`\"']?(\w+)[`\"']?\s*\(([^)]+)\)", cols_section, re.IGNORECASE):
            from_cols = re.findall(r"[`\"']?(\w+)[`\"']?", fk_match.group(1))
            to_table = fk_match.group(2)
            to_cols = re.findall(r"[`\"']?(\w+)[`\"']?", fk_match.group(3))
            fks.append({
                "from_cols": from_cols,
                "to_table": to_table,
                "to_cols": to_cols
            })

        schema.append({
            "name": table_name,
            "primary_keys": pks,
            "foreign_keys": fks
        })
    return schema


def extract_table_data(sql_content: str, table_name: str):
    """Extract columns and rows for a specific table only."""
    # Find CREATE TABLE for this table - extract body between outer parentheses
    create_start = re.search(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?" + re.escape(table_name) + r"[`\"']?\s*\(",
        sql_content,
        re.IGNORECASE
    )
    if not create_start:
        return [], []

    start = create_start.end()
    depth = 1
    i = start
    while i < len(sql_content) and depth > 0:
        ch = sql_content[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        i += 1

    cols_section = sql_content[start:i-1]

    columns = []
    pks = []
    fks = []
    for col_match in re.finditer(r"[`\"']?(\w+)[`\"']?\s+[^,]*?PRIMARY\s+KEY", cols_section, re.IGNORECASE):
        col_name = col_match.group(1)
        if col_name.upper() not in ("PRIMARY", "KEY", "INDEX", "UNIQUE", "CONSTRAINT", "FOREIGN", "CHECK"):
            pks.append(col_name)
            
    pk_match = re.search(r"PRIMARY\s+KEY\s*\(([^)]+)\)", cols_section, re.IGNORECASE)
    if pk_match:
        pk_cols = re.findall(r"[`\"']?(\w+)[`\"']?", pk_match.group(1))
        for c in pk_cols:
            if c not in pks:
                pks.append(c)
                
    for fk_match in re.finditer(r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+[`\"']?(\w+)[`\"']?\s*\(([^)]+)\)", cols_section, re.IGNORECASE):
        from_cols = re.findall(r"[`\"']?(\w+)[`\"']?", fk_match.group(1))
        to_table = fk_match.group(2)
        to_cols = re.findall(r"[`\"']?(\w+)[`\"']?", fk_match.group(3))
        fks.append({
            "from_cols": from_cols,
            "to_table": to_table,
            "to_cols": to_cols
        })

    for col_match in re.finditer(r"[`\"']?(\w+)[`\"']?\s+(\w+(?:\s*\([^)]*\))?)", cols_section, re.IGNORECASE):
        col_name = col_match.group(1)
        col_type = col_match.group(2).strip().upper()
        if col_name.upper() in ("PRIMARY", "KEY", "INDEX", "UNIQUE", "CONSTRAINT", "FOREIGN", "CHECK", "NOT", "DEFAULT", "NULL", "AUTO_INCREMENT", "IF", "FULLTEXT", "SPATIAL"):
            continue
        columns.append({"name": col_name, "type": col_type, "is_pk": col_name in pks})

    # Find INSERT INTO for this table
    insert_pattern = re.compile(
        r"INSERT\s+(?:IGNORE\s+)?INTO\s+[`\"']?" + re.escape(table_name) + r"[`\"']?(?:\s*\([^)]*\))?\s+VALUES\s*",
        re.IGNORECASE
    )
    rows = []
    for insert_match in insert_pattern.finditer(sql_content):
        start_idx = insert_match.end()
        i = start_idx
        in_string = False
        while i < len(sql_content):
            if sql_content[i] == "'" and (i == 0 or sql_content[i-1] != "\\"):
                in_string = not in_string
            elif sql_content[i] == ";" and not in_string:
                break
            i += 1
        values_str = sql_content[start_idx:i]
        rows.extend(_parse_values(values_str))

    return columns, rows, pks, fks


def _rows_to_dicts(columns, rows):
    if not columns or not rows:
        return rows
    column_names = [c["name"] for c in columns]
    return [dict(zip(column_names, row)) for row in rows]


def _parse_values(values_str: str):
    rows = []
    i = 0
    while i < len(values_str):
        if values_str[i] == "(":
            depth = 1
            j = i + 1
            while j < len(values_str) and depth > 0:
                if values_str[j] == "(":
                    depth += 1
                elif values_str[j] == ")":
                    depth -= 1
                j += 1
            row_str = values_str[i + 1:j - 1]
            row_values = _parse_row_values(row_str)
            rows.append(row_values)
            i = j
        else:
            i += 1
    return rows


def _parse_row_values(row_str: str):
    values = []
    i = 0
    while i < len(row_str):
        if row_str[i] in " ,":
            i += 1
            continue
        if row_str[i:].upper().startswith("NULL"):
            values.append(None)
            i += 4
            continue
        if row_str[i] == "'":
            j = i + 1
            while j < len(row_str):
                if row_str[j] == "\\":
                    j += 2
                    continue
                if row_str[j] == "'":
                    if j + 1 < len(row_str) and row_str[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
            val = row_str[i + 1:j].replace("''", "'").replace("\\'", "'").replace("\\\\", "\\")
            values.append(val)
            i = j + 1
            continue
        j = i
        while j < len(row_str) and row_str[j] not in ",)":
            j += 1
            if j < len(row_str) and row_str[j] == "'" and row_str[j-1] != "\\":
                break
        val = row_str[i:j].strip()
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
