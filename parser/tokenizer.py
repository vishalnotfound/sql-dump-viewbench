from enum import Enum
from typing import Iterator, Optional, Tuple


class TokenType(Enum):
    # Keywords
    CREATE = "CREATE"
    TABLE = "TABLE"
    INSERT = "INSERT"
    INTO = "INTO"
    VALUES = "VALUES"
    NULL = "NULL"
    # Operators
    COMMA = ","
    LPAREN = "("
    RPAREN = ")"
    SEMICOLON = ";"
    # Literals
    STRING = "STRING"
    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"
    # Other
    COMMENT = "COMMENT"
    EOF = "EOF"


class Token:
    def __init__(self, type: TokenType, value: str = ""):
        self.type = type
        self.value = value

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)})"


class Tokenizer:
    def __init__(self, sql: str):
        self.sql = sql
        self.pos = 0
        self.len = len(sql)

    def peek(self, offset: int = 0) -> Optional[str]:
        pos = self.pos + offset
        if pos >= self.len:
            return None
        return self.sql[pos]

    def advance(self, n: int = 1) -> None:
        self.pos += n

    def skip_whitespace(self) -> None:
        while self.peek() and self.peek().isspace():
            self.advance()

    def read_comment(self) -> Optional[Token]:
        if self.peek() == "-" and self.peek(1) == "-":
            # Line comment
            start = self.pos
            while self.peek() and self.peek() != "\n":
                self.advance()
            self.advance()
            return Token(TokenType.COMMENT, self.sql[start : self.pos])
        elif self.peek() == "/" and self.peek(1) == "*":
            # Block comment
            start = self.pos
            self.advance(2)
            while self.peek() is not None:
                if self.peek() == "*" and self.peek(1) == "/":
                    self.advance(2)
                    break
                self.advance()
            return Token(TokenType.COMMENT, self.sql[start : self.pos])
        elif self.peek() == "#":
            # MySQL-style comment
            start = self.pos
            while self.peek() and self.peek() != "\n":
                self.advance()
            self.advance()
            return Token(TokenType.COMMENT, self.sql[start : self.pos])
        return None

    def read_string(self) -> Token:
        quote = self.peek()
        self.advance()
        start = self.pos
        while self.peek() is not None:
            if self.peek() == "\\":
                # Escape
                self.advance(2)
            elif self.peek() == quote:
                break
            else:
                self.advance()
        value = self.sql[start : self.pos]
        self.advance()
        return Token(TokenType.STRING, value)

    def read_identifier(self) -> Token:
        start = self.pos
        while self.peek() and (self.peek().isalnum() or self.peek() in "_`"):
            self.advance()
        value = self.sql[start : self.pos]
        # Strip backticks if any
        if value.startswith("`") and value.endswith("`"):
            value = value[1:-1]
        # Check for keywords
        upper = value.upper()
        if upper in ["CREATE", "TABLE", "INSERT", "INTO", "VALUES", "NULL"]:
            return Token(TokenType[upper], value)
        return Token(TokenType.IDENTIFIER, value)

    def read_number(self) -> Token:
        start = self.pos
        while self.peek() and (self.peek().isdigit() or self.peek() in ".+-"):
            self.advance()
        return Token(TokenType.NUMBER, self.sql[start : self.pos])

    def tokenize(self) -> Iterator[Token]:
        while self.pos < self.len:
            self.skip_whitespace()
            if self.pos >= self.len:
                break
            # Check comments
            comment = self.read_comment()
            if comment:
                yield comment
                continue
            # Check other tokens
            char = self.peek()
            if char in "'\"":
                yield self.read_string()
            elif char in "_`" or char.isalpha():
                yield self.read_identifier()
            elif char in "0123456789":
                yield self.read_number()
            elif char == ",":
                self.advance()
                yield Token(TokenType.COMMA, ",")
            elif char == "(":
                self.advance()
                yield Token(TokenType.LPAREN, "(")
            elif char == ")":
                self.advance()
                yield Token(TokenType.RPAREN, ")")
            elif char == ";":
                self.advance()
                yield Token(TokenType.SEMICOLON, ";")
            else:
                # Skip unknown characters
                self.advance()
        yield Token(TokenType.EOF, "")
