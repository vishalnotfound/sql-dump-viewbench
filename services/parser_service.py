from pathlib import Path
from typing import Generator
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.tokenizer import Tokenizer
from parser.parser import Parser
from parser.models import ParsedSQL


class ParserService:
    def parse_sql_file(self, file_path: Path) -> ParsedSQL:
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()
        tokenizer = Tokenizer(sql)
        parser = Parser(tokenizer)
        return parser.parse()
