import sys
from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def tqdm_output(tqdm, write=sys.stderr.write):
    def wrapper(message):
        if message != "\n":
            tqdm.clear()
        write(message)
        if "\n" in message:
            tqdm.display()

    with patch("sys.stdout", sys.stderr), patch("sys.stderr.write", wrapper):
        yield tqdm
