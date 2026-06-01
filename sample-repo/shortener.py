"""In-memory URL shortener: encode/decode short codes and track click counts."""

import string

ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
BASE = len(ALPHABET)


def encode(num):
    """Convert a non-negative integer id into a short base-62 code."""
    if num == 0:
        return ALPHABET[0]
    chars = []
    while num > 0:
        num, rem = divmod(num, BASE)
        chars.append(ALPHABET[rem])
    return "".join(reversed(chars))


def decode(code):
    """Convert a base-62 code back into its integer id."""
    num = 0
    for ch in code:
        num = num * BASE + ALPHABET.index(ch)
    return num


class Shortener:
    def __init__(self):
        self._urls = {}
        self._clicks = {}
        self._next_id = 1

    def shorten(self, url):
        code = encode(self._next_id)
        self._urls[code] = url
        self._clicks[code] = 0
        self._next_id += 1
        return code

    def resolve(self, code):
        if code not in self._urls:
            raise KeyError(f"unknown code: {code}")
        self._clicks[code] += 1
        return self._urls[code]

    def stats(self, code):
        return {"url": self._urls[code], "clicks": self._clicks[code]}
