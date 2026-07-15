from typing import Iterator, Any, Optional
from .tokenizer import Tokenizer, Token, TokenType
from .models import Table, Column, ParsedSQL


class Parser:
    def __init__(self, tokenizer: Tokenizer):
        self.tokenizer = tokenizer
        self.tokens = list(tokenizer.tokenize())
        self.pos = 0
        self.parsed = ParsedSQL()

    def peek(self, offset: int = 0) -> Optional[Token]:
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return None
        return self.tokens[pos]

    def advance(self, n: int = 1) -> Token:
        token = self.tokens[self.pos]
        self.pos += n
        return token

    def skip_until(self, *token_types: TokenType) -> None:
        while self.peek() and self.peek().type not in token_types:
            self.advance()

    def parse_create_table(self) -> Optional[Table]:
        # Skip CREATE TABLE
        self.advance(2)
        # Get table name
        if self.peek() and self.peek().type == TokenType.IDENTIFIER:
            table_name = self.advance().value
        else:
            return None
        # Skip IF NOT EXISTS if present
        if self.peek() and self.peek().type == TokenType.IDENTIFIER and self.peek().value.upper() == "IF":
            self.advance(3)
        # Expect (
        if not (self.peek() and self.peek().type == TokenType.LPAREN):
            return None
        self.advance()
        # Parse columns
        columns = []
        while self.peek() and self.peek().type != TokenType.RPAREN:
            col_token = self.peek()
            if col_token and col_token.type == TokenType.IDENTIFIER:
                # Check if this is a constraint (PRIMARY, KEY, FOREIGN, etc.)
                upper_val = col_token.value.upper()
                if upper_val in ["PRIMARY", "KEY", "FOREIGN", "UNIQUE", "INDEX", "CONSTRAINT"]:
                    # Skip entire constraint until next comma or )
                    while (self.peek() and 
                           self.peek().type != TokenType.COMMA and 
                           self.peek().type != TokenType.RPAREN):
                        self.advance()
                else:
                    col_name = self.advance().value
                    # Get type
                    if self.peek() and self.peek().type == TokenType.IDENTIFIER:
                        col_type = self.advance().value
                        # Check for length modifiers like (255)
                        if self.peek() and self.peek().type == TokenType.LPAREN:
                            self.skip_until(TokenType.RPAREN)
                            self.advance()
                        # Skip constraints (NULL, NOT NULL, PRIMARY KEY, etc.)
                        while (self.peek() and 
                               self.peek().type != TokenType.COMMA and 
                               self.peek().type != TokenType.RPAREN):
                            self.advance()
                        columns.append(Column(name=col_name, type=col_type))
            if self.peek() and self.peek().type == TokenType.COMMA:
                self.advance()
        # Skip )
        if self.peek() and self.peek().type == TokenType.RPAREN:
            self.advance()
        # Skip table options (ENGINE, CHARSET, etc.)
        while self.peek() and self.peek().type != TokenType.SEMICOLON:
            self.advance()
        if self.peek() and self.peek().type == TokenType.SEMICOLON:
            self.advance()
        return Table(name=table_name, columns=columns)

    def parse_insert_into(self) -> Optional[tuple[str, list[list[Any]]]]:
        # Skip INSERT INTO
        self.advance(2)
        # Get table name
        if self.peek() and self.peek().type == TokenType.IDENTIFIER:
            table_name = self.advance().value
        else:
            return None
        # Skip (columns) if present
        if self.peek() and self.peek().type == TokenType.LPAREN:
            self.skip_until(TokenType.RPAREN)
            self.advance()
        # Skip VALUES
        if not (self.peek() and self.peek().type == TokenType.VALUES):
            return None
        self.advance()
        # Parse value tuples
        rows = []
        while self.peek() and self.peek().type == TokenType.LPAREN:
            self.advance()
            row = []
            while self.peek() and self.peek().type != TokenType.RPAREN:
                token = self.peek()
                if token.type == TokenType.STRING:
                    row.append(token.value)
                elif token.type == TokenType.NUMBER:
                    row.append(token.value)
                elif token.type == TokenType.NULL:
                    row.append(None)
                self.advance()
                if self.peek() and self.peek().type == TokenType.COMMA:
                    self.advance()
            if self.peek() and self.peek().type == TokenType.RPAREN:
                self.advance()
            rows.append(row)
            if self.peek() and self.peek().type == TokenType.COMMA:
                self.advance()
            else:
                break
        # Skip until ;
        if self.peek() and self.peek().type == TokenType.SEMICOLON:
            self.advance()
        return (table_name, rows)

    def parse(self) -> ParsedSQL:
        while self.peek() and self.peek().type != TokenType.EOF:
            token = self.peek()
            if token.type == TokenType.CREATE and self.peek(1) and self.peek(1).type == TokenType.TABLE:
                table = self.parse_create_table()
                if table:
                    self.parsed.tables[table.name] = table
            elif token.type == TokenType.INSERT and self.peek(1) and self.peek(1).type == TokenType.INTO:
                result = self.parse_insert_into()
                if result:
                    table_name, rows = result
                    if table_name in self.parsed.tables:
                        self.parsed.tables[table_name].rows.extend(rows)
            else:
                self.advance()
        return self.parsed
