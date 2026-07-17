import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from services.file_service import SQLParser

sql_path = Path(__file__).parent.parent / 'sql' / 'kmaytxkd_collarchecktest.sql'
with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

for line_count in [50000, 75000, 100000, 120000]:
    chunk = ''.join(lines[:line_count])
    start = time.time()
    parser = SQLParser()
    result = parser.parse(chunk)
    elapsed = time.time() - start
    print(f'Lines {line_count}: {elapsed:.2f}s, tables={len(result["tables"])}, rows={result["total_rows"]}')
