from io import StringIO

from ._parser import RSONParser
from ._types import Stream, ParseResult

def load(stream: Stream) -> ParseResult:
    return RSONParser(stream).parse()


def loads(string: str) -> ParseResult:
    return load(StringIO(string))
