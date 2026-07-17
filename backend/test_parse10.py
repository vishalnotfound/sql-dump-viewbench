import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Monkey-patch SQLParser to add timing
from services.file_service import SQLParser

original_parse_insert_into = SQLParser._parse_insert_into
original_parse_values = SQLParser._parse_values
original_parse_row_values = SQLParser._parse_row_values

def timed_parse_insert_into(self, sql):
    start = time.time()
    result = original_parse_insert_into(self, sql)
    elapsed = time.time() - start
    if elapsed > 0.05:
        print(f'  _parse_insert_into took {elapsed:.2f}s')
    return result

def timed_parse_values(self, values_str):
    start = time.time()
    result = original_parse_values(self, values_str)
    elapsed = time.time() - start
    if elapsed > 0.05:
        print(f'  _parse_values took {elapsed:.2f}s, len={len(values_str)}, rows={len(result)}')
    return result

def timed_parse_row_values(self, row_str):
    start = time.time()
    result = original_parse_row_values(self, row_str)
    elapsed = time.time() - start
    if elapsed > 0.05:
        print(f'  _parse_row_values took {elapsed:.2f}s, len={len(row_str)}')
    return result

SQLParser._parse_insert_into = timed_parse_insert_into
SQLParser._parse_values = timed_parse_values
SQLParser._parse_row_values = timed_parse_row_values

sql_path = Path(__file__).parent.parent / 'sql' / 'kmaytxkd_collarchecktest.sql'
with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read(15000000)  # 15MB

print(f'Loaded {len(content)} chars')
start = time.time()
parser = SQLParser()
result = parser.parse(content)
elapsed = time.time() - start
print(f'Total: {elapsed:.2f}s, tables={len(result["tables"])}, rows={result["total_rows"]}')
