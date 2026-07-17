import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from services.file_service import SQLParser

sql_path = Path(__file__).parent.parent / 'sql' / 'kmaytxkd_collarchecktest.sql'
with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

print(f'Total size: {len(content)}')
start = time.time()
parser = SQLParser()
result = parser.parse(content)
elapsed = time.time() - start
print(f'Parsed in {elapsed:.2f}s')
print(f'Tables: {len(result["tables"])}, rows: {result["total_rows"]}')
