import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from services.file_service import SQLParser

sql_path = Path(__file__).parent.parent / 'sql' / 'kmaytxkd_collarchecktest.sql'
with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read(2000000)

parser = SQLParser()
sql_content = content.replace("\r\n", "\n")
lines = sql_content.split("\n")

i = 0
insert_num = 0
while i < len(lines):
    line = lines[i].strip()
    if not line or line.startswith("--") or line.startswith("#"):
        i += 1
        continue

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
        continue

    if line.upper().startswith("INSERT INTO"):
        insert_num += 1
        insert_lines = [line]
        i += 1
        while i < len(lines):
            stripped = lines[i].strip()
            insert_lines.append(stripped)
            if stripped.endswith(";"):
                i += 1
                break
            i += 1
        
        sql = "\n".join(insert_lines)
        start = time.time()
        parser._parse_insert_into(sql)
        elapsed = time.time() - start
        if elapsed > 0.1:
            print(f'INSERT {insert_num} took {elapsed:.2f}s, rows so far: {sum(len(t["rows"]) for t in parser.tables.values())}')
            print(f'  SQL length: {len(sql)}')
            print(f'  First 200 chars: {sql[:200]}')
        continue

    i += 1

print(f'Total tables: {len(parser.tables)}')
print(f'Total rows: {sum(len(t["rows"]) for t in parser.tables.values())}')
