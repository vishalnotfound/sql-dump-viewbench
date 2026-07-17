from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Column:
    name: str
    type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False


@dataclass
class Table:
    name: str
    columns: List[Column] = field(default_factory=list)
    rows: List[List[Any]] = field(default_factory=list)


@dataclass
class ParsedSQL:
    tables: Dict[str, Table] = field(default_factory=dict)
