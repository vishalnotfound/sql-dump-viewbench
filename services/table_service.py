from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.cache_service import CacheService


class TableService:
    def __init__(self, cache_dir: Path):
        self.cache_service = CacheService(cache_dir)

    def get_tables(self, sql_file_path: Path) -> List[Dict[str, Any]]:
        manager = self.cache_service.get_manager(sql_file_path)
        return manager.get_tables()

    def get_table_data(
        self,
        sql_file_path: Path,
        table_name: str,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        order: str = "asc",
    ) -> Dict[str, Any]:
        manager = self.cache_service.get_manager(sql_file_path)
        return manager.get_table_data(
            table_name, page, page_size, search, sort, order
        )

    def get_metadata(self, sql_file_path: Path) -> Dict[str, Any]:
        manager = self.cache_service.get_manager(sql_file_path)
        return manager.get_metadata()
