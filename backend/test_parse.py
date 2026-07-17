import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from services.file_service import SQLParser

start = time.time()
sql_path = Path(__file__).parent.parent / 'sql' / 'kmaytxkd_collarchecktest.sql'
with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read(500000)

print(f'Read partial content in {time.time() - start:.1f}s')
parser = SQLParser()
result = parser.parse(content)
print(f'Parsed in {time.time() - start:.1f}s')
print(f'Tables: {len(result["tables"])}, rows: {result["total_rows"]}')
for name in list(result['tables'].keys())[:3]:
    t = result['tables'][name]
    print(f'  {name}: cols={len(t["columns"])}, rows={len(t["rows"])}')
