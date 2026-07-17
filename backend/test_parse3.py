import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from services.file_service import SQLParser

sql_path = Path(__file__).parent.parent / 'sql' / 'kmaytxkd_collarchecktest.sql'
with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read(2000000)  # 2MB max

print(f'Loaded {len(content)} chars')

# Let's trace the parser
parser = SQLParser()
sql_content = content.replace("\r\n", "\n")
lines = sql_content.split("\n")
print(f'Total lines: {len(lines)}')

create_count = 0
insert_count = 0
i = 0
start = time.time()

while i < len(lines):
    line = lines[i].strip()
    if not line or line.startswith("--") or line.startswith("#"):
        i += 1
        continue

    if line.upper().startswith("CREATE TABLE"):
        create_count += 1
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
        insert_count += 1
        insert_lines = [line]
        i += 1
        while i < len(lines):
            stripped = lines[i].strip()
            insert_lines.append(stripped)
            if stripped.endswith(";"):
                i += 1
                break
            i += 1
        continue

    i += 1

elapsed = time.time() - start
print(f'Collection done in {elapsed:.2f}s')
print(f'CREATE tables: {create_count}, INSERT statements: {insert_count}')
print(f'Last few lines:')
for j in range(max(0, i-5), min(i, len(lines))):
    print(f'  {j}: {lines[j][:80]}')
