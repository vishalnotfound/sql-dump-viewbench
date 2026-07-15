from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from fastapi import UploadFile
import aiofiles


class FileService:
    def __init__(self, sql_dir: Path):
        self.sql_dir = sql_dir
        # Ensure sql_dir exists
        self.sql_dir.mkdir(exist_ok=True)

    def get_sql_files(self) -> List[Dict[str, Any]]:
        files = []
        for file in self.sql_dir.glob("*.sql"):
            stat = file.stat()
            files.append({
                "name": file.name,
                "size": self._format_size(stat.st_size),
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        return files

    def get_sql_file_path(self, filename: str) -> Path:
        return self.sql_dir / filename

    async def save_uploaded_file(self, file: UploadFile) -> Dict[str, Any]:
        # Save the uploaded file to sql_dir
        file_path = self.sql_dir / file.filename
        # Write the file
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        # Return file info
        stat = file_path.stat()
        return {
            "name": file.filename,
            "size": self._format_size(stat.st_size),
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

    def delete_file(self, filename: str) -> bool:
        file_path = self.sql_dir / filename
        if file_path.exists():
            file_path.unlink()
            # Also delete cache
            cache_path = Path("cache") / f"{filename}.sqlite"
            if cache_path.exists():
                cache_path.unlink()
            return True
        return False

    def _format_size(self, bytes_size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} TB"
