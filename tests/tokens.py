import sys

from src.rson._parser import _Private


try:
    FILE_NAME = sys.argv[1]
except IndexError:
    print("Usage: python tokens <file>")
    sys.exit(1)


with open(FILE_NAME, encoding="utf-8") as f:
    tokenizer = _Private.RSONTokenizer(f)

    while not tokenizer.eof:
        token = tokenizer.token

        print(f"{token.type} ({token.start.line}:{token.start.column}-{token.end.line}:{token.end.column}): {token.value}")

        tokenizer.next()
