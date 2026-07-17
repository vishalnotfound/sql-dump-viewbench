import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from services.file_service import SQLParser

sql_path = Path(__file__).parent.parent / 'sql' / 'kmaytxkd_collarchecktest.sql'
with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

sizes = [10500000, 10800000, 11000000, 11200000]
for size in sizes:
    chunk = content[:size]
    start = time.time()
    parser = SQLParser()
    result = parser.parse(chunk)
    elapsed = time.time() - start
    print(f'Size {size}: {elapsed:.2f}s, tables={len(result["tables"])}, rows={result["total_rows"]}')
