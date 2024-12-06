from dataclasses import dataclass
from enum import Enum

from ._types import ParseResult, Stream


class _Private:
    L_CURLY = "{"
    R_CURLY = "}"

    L_SQUARE = "["
    R_SQUARE = "]"

    L_PAREN = "("
    R_PAREN = ")"

    COMMA = ","
    COLON = ":"

    QUOTE = "\""

    DOLLAR = "$"

    BACKSLASH = "\\"
    SLASH = "/"
    STAR = "*"

    WHITESPACE = {" ", "\t", "\n", "\r"}

    DIGITS = "0123456789"
    DIGITS_1_9 = "123456789"

    DEF_FIRST = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    DEF = DEF_FIRST + DIGITS

    class RSONTokenType(Enum):
        L_CURLY = "Sym.LCurly"
        R_CURLY = "Sym.RCurly"

        L_SQUARE = "Sym.LSquare"
        R_SQUARE = "Sym.RSquare"

        COMMA = "Sym.Comma"
        COLON = "Sym.Colon"

        STRING = "Lit.Str"
        NUMBER = "Lit.Num"
        REF = "Lit.Ref"
        DEF = "Lit.Def"

        TRUE = "Lit.True"
        FALSE = "Lit.False"
        NULL = "Lit.Null"

        WS = "WS"
        COMMENT = "WS.Comment"

        EOF = "EOF"

        def is_whitespace(self):
            return self.value.startswith("WS")

    @dataclass(frozen=True)
    class RSONToken:
        type: "_Private.RSONTokenType"
        value: str
        start: "_Private.Position"
        end: "_Private.Position"


    class Position:
        def __init__(self, line: int = 1, column: int = 1):
            self.line = line
            self.column = column

        def next_line(self) -> int:
            self.line += 1
            self.column = 1

        def next_column(self, by: int = 1) -> int:
            self.column += by

        def copy(self) -> "_Private.Position":
            return _Private.Position(self.line, self.column)
            

    class RSONTokenizer:
        def __init__(self, stream: Stream):
            self._stream = stream
            self._token: _Private.RSONToken
            self._position = _Private.Position()
            self._start = self._position.copy()

            self._next()

        @property
        def token(self) -> "_Private.RSONToken":
            return self._token
        
        @property
        def eof(self) -> bool:
            return self._token.type == _Private.RSONTokenType.EOF
        
        def _create_token(self, type: "_Private.RSONTokenType", value: str) -> "_Private.RSONToken":
            self._token = _Private.RSONToken(type, value, self._start, self._position)
            self._start = self._position.copy()
            return self._token

        def next(self) -> "_Private.RSONToken":
            if self.eof:
                return self._token
            
            self._next()

            while not self.eof and self.token.type.is_whitespace():
                self._next()

            return self.token
            
        def _next(self):
            char = self._peek()
            if not char:
                return self._create_token(_Private.RSONTokenType.EOF, "")
            
            if char == "\n":
                token = self._create_token(_Private.RSONTokenType.WS, self._read(1))
                self._position.next_line()
                return token
            elif char in _Private.WHITESPACE:
                return self._create_token(_Private.RSONTokenType.WS, self._read(1))
            elif char == _Private.SLASH:
                self._read(1)
                char = self._peek()
                if char == _Private.SLASH:
                    while self._peek() not in { "\n", "" }:
                        self._read(1)
                    comment = self._create_token(_Private.RSONTokenType.COMMENT, "// {LINE}")
                    self._position.next_line()
                    return comment
                elif char == _Private.STAR:
                    comment = self._read(2)
                    while True:
                        char = self._read(1)
                        if not char:
                            break
                        if char == _Private.STAR and self._peek() == _Private.SLASH:
                            self._read(1)
                            break
                    return self._create_token(_Private.RSONTokenType.COMMENT, "/* {BLOCK} */")
                else:
                    self.error(char)
            elif char == _Private.L_CURLY:
                return self._create_token(_Private.RSONTokenType.L_CURLY, self._read(1))
            elif char == _Private.R_CURLY:
                return self._create_token(_Private.RSONTokenType.R_CURLY, self._read(1))
            elif char == _Private.L_SQUARE:
                return self._create_token(_Private.RSONTokenType.L_SQUARE, self._read(1))
            elif char == _Private.R_SQUARE:
                return self._create_token(_Private.RSONTokenType.R_SQUARE, self._read(1))
            elif char == _Private.COMMA:
                return self._create_token(_Private.RSONTokenType.COMMA, self._read(1))
            elif char == _Private.COLON:
                return self._create_token(_Private.RSONTokenType.COLON, self._read(1))
            elif char == _Private.QUOTE:
                return self._create_token(_Private.RSONTokenType.STRING, self._string())
            elif char in _Private.DIGITS or char == "-":
                return self._create_token(_Private.RSONTokenType.NUMBER, self._number())
            elif char == _Private.L_PAREN:
                self._read(1)
                if self._peek() not in _Private.DEF_FIRST:
                    self.error(char)
                value = self._ref_name()
                if (char := self._read(1)) != _Private.R_PAREN:
                    self.error(char, _Private.R_PAREN)
                return self._create_token(_Private.RSONTokenType.DEF, value)
            elif char == _Private.DOLLAR:
                self._read(1)
                if self._peek() not in _Private.DEF_FIRST:
                    self.error(char)
                return self._create_token(_Private.RSONTokenType.REF, self._ref_name())
            elif char == "t":
                self._read(1)
                if self._read(3) != "rue":
                    self.error(char)
                return self._create_token(_Private.RSONTokenType.TRUE, "true")
            elif char == "f":
                self._read(1)
                if self._read(4) != "alse":
                    self.error(char)
                return self._create_token(_Private.RSONTokenType.FALSE, "false")
            elif char == "n":
                self._read(1)
                if self._read(3) != "ull":
                    self.error(char)
                return self._create_token(_Private.RSONTokenType.NULL, "null")
            else:
                self.error(char)

        def error(self, char: str):
            raise ValueError(f"Unexpected character {char} at {self._position.line}:{self._position.column}")
        
        def unexpected_eof(self):
            raise ValueError("Unexpected EOF")
        
        def _string(self) -> str:
            self._read(1)

            value = ""

            while (char := self._peek()) != _Private.QUOTE:
                if not char:
                    self.unexpected_eof()
                
                if char == _Private.BACKSLASH:
                    self._read(1)
                    char = self._peek()
                    if char == _Private.QUOTE:
                        char = _Private.QUOTE
                    elif char == _Private.BACKSLASH:
                        char = _Private.BACKSLASH
                    elif char == _Private.SLASH:
                        char = _Private.SLASH
                    elif char == "b":
                        char = "\b"
                    elif char == "f":
                        char = "\f"
                    elif char == "n":
                        char = "\n"
                    elif char == "r":
                        char = "\r"
                    elif char == "t":
                        char = "\t"
                    elif char == "u":
                        self._read(1)
                        char = chr(int(self._read(4), 16))
                    else:
                        self.error(char)
                    
                value += char
                self._read(1)

            self._read(1)

            return value

        def _number(self) -> str:
            value = self._read(1)

            if value == "0":
                if self._peek() != ".":
                    return value
                value += self._read(1)
                while self._peek() in _Private.DIGITS:
                    value += self._read(1)
            else:
                while self._peek() in _Private.DIGITS:
                    value += self._read(1)
                if self._peek() == ".":
                    value += self._read(1)
                    while self._peek() in _Private.DIGITS:
                        value += self._read(1)
            
            if self._peek() in { "e", "E" }:
                value += self._read(1)
                if self._peek() in { "+", "-" }:
                    value += self._read(1)
                while self._peek() in _Private.DIGITS:
                    value += self._read(1)

            return value

        def _ref_name(self) -> str:
            value = self._read(1)

            while self._peek() in _Private.DEF:
                value += self._read(1)

            return value

        def _peek(self) -> str:
            pos = self._stream.tell()
            value = self._stream.read(1)
            if value:
                self._stream.seek(pos, 0)
            return value

        def _read(self, n: int) -> str:
            value = self._stream.read(n)
            self._position.next_column(n)
            return value

    class RSONParser:
        def __init__(self, stream: Stream):
            self._tokenizer = _Private.RSONTokenizer(stream)
            self._ref = {}
            self._late = []

        def parse(self) -> ParseResult:
            if self._tokenizer.eof:
                raise ValueError("Unexpected EOF")

            result = self.parse_value()

            for obj, key, ref in self._late:
                if isinstance(obj, dict):
                    obj[key] = self._ref[ref]
                else:
                    obj.insert(key, self._ref[ref])

            return result

        def token(self, type: "_Private.RSONTokenType", eat: bool = False) -> bool:
            if self._tokenizer.token.type == type:
                if eat:
                    self._tokenizer.next()
                return True
            return False

        def eat(self, value: str | None):
            token = self._tokenizer.token
            if not self.token(value, eat=True):
                raise ValueError(f"Expected {value} at {token.start.line}:{token.start.column}")
            return token

        def parse_value(self) -> ParseResult:
            value: ParseResult

            if self.token(_Private.RSONTokenType.L_CURLY):
                value = self.parse_object()
            
            elif self.token(_Private.RSONTokenType.L_SQUARE):
                value = self.parse_array()
            
            elif self.token(_Private.RSONTokenType.STRING):
                value = self.eat(_Private.RSONTokenType.STRING).value
            
            elif self.token(_Private.RSONTokenType.NUMBER):
                value = self.eat(_Private.RSONTokenType.NUMBER).value
                if value.isdigit():
                    value = int(value)
                else:
                    value = float(value)
            
            elif self.token(_Private.RSONTokenType.TRUE, eat=True):
                value = True
            
            elif self.token(_Private.RSONTokenType.FALSE, eat=True):
                value = False
            
            elif self.token(_Private.RSONTokenType.NULL, eat=True):
                value = None
            
            else:
                raise ValueError(f"Unexpected token {self._tokenizer.token}")
            
            if self.token(_Private.RSONTokenType.DEF):
                self._ref[self.eat(_Private.RSONTokenType.DEF).value] = value
            
            return value

        def parse_object(self) -> ParseResult:
            self.eat(_Private.RSONTokenType.L_CURLY)

            result = {}

            while not self.token(_Private.RSONTokenType.R_CURLY):
                key = self.eat(_Private.RSONTokenType.STRING).value

                self.eat(_Private.RSONTokenType.COLON)

                if self.token(_Private.RSONTokenType.REF):
                    ref = self.eat(_Private.RSONTokenType.REF).value
                    if ref not in self._ref:
                        self._late.append((result, key, ref))
                    else:
                        result[key] = self._ref[ref]
                else:
                    result[key] = self.parse_value()

                if not self.token(_Private.RSONTokenType.COMMA, eat=True):
                    break

            self.eat(_Private.RSONTokenType.R_CURLY)

            return result

        def parse_array(self) -> ParseResult:
            self.eat(_Private.RSONTokenType.L_SQUARE)

            result = []

            while not self.token(_Private.RSONTokenType.R_SQUARE):
                if self.token(_Private.RSONTokenType.REF):
                    ref = self.eat(_Private.RSONTokenType.REF).value
                    if ref not in self._ref:
                        self._late.append((result, len(result), ref))
                    else:
                        result.append(self._ref[ref])
                else:
                    result.append(self.parse_value())

                if not self.token(_Private.RSONTokenType.COMMA, eat=True):
                    break

            self.eat(_Private.RSONTokenType.R_SQUARE)

            return result
        

RSONParser = _Private.RSONParser


__all__ = ["RSONParser"]
