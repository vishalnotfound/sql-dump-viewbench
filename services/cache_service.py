from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.sqlite_manager import SQLiteManager
from services.parser_service import ParserService


class CacheService:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.parser_service = ParserService()

    def get_manager(self, sql_file_path: Path) -> SQLiteManager:
        manager = SQLiteManager(sql_file_path, self.cache_dir)
        # Check if cache is valid
        if not manager.is_cache_valid():
            # Parse and create cache
            parsed = self.parser_service.parse_sql_file(sql_file_path)
            manager.create_cache(parsed)
        return manager
