from src.rson import load


with open("test.rson") as f:
    print(load(f))
