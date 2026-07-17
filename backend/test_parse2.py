import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from services.file_service import SQLParser

sql_path = Path(__file__).parent.parent / 'sql' / 'kmaytxkd_collarchecktest.sql'
with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

print(f'Total file size: {len(content)} chars')

chunk_size = 1000000
offset = 0
parser = SQLParser()

while offset < len(content):
    chunk = content[offset:offset+chunk_size]
    start = time.time()
    result = parser.parse(chunk)
    elapsed = time.time() - start
    print(f'Offset {offset}: parsed in {elapsed:.2f}s, tables={len(result["tables"])}, rows={result["total_rows"]}')
    offset += chunk_size
