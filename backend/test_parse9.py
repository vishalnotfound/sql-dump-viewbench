import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from services.file_service import SQLParser

sql_path = Path(__file__).parent.parent / 'sql' / 'kmaytxkd_collarchecktest.sql'
with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

chunk = content[:10500000]
lines = chunk.split('\n')
print(f'Total lines in chunk: {len(lines)}')
print(f'Last 5 lines:')
for i in range(max(0, len(lines)-5), len(lines)):
    print(f'  {i}: {lines[i][:100]}')
