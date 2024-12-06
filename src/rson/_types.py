from typing import TypeAlias, TextIO, Union


Stream: TypeAlias = TextIO
ParseResult: TypeAlias = Union[None, int, float, str, bool, list, dict]
