"""URL shortener: encode/decode short codes and track click counts.

State is kept in memory by default. Pass a file path to persist it across
process invocations (used by the CLI so codes survive between commands).
"""

import json
import os
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
    def __init__(self, path=None):
        self._path = path
        self._urls = {}
        self._clicks = {}
        self._next_id = 1
        if path and os.path.exists(path):
            self._load()

    def _load(self):
        with open(self._path) as f:
            data = json.load(f)
        self._urls = data["urls"]
        self._clicks = data["clicks"]
        self._next_id = data["next_id"]

    def _save(self):
        if not self._path:
            return
        with open(self._path, "w") as f:
            json.dump(
                {"urls": self._urls, "clicks": self._clicks, "next_id": self._next_id},
                f,
            )

    def shorten(self, url):
        code = encode(self._next_id)
        self._urls[code] = url
        self._clicks[code] = 0
        self._next_id += 1
        self._save()
        return code

    def resolve(self, code):
        if code not in self._urls:
            raise KeyError(f"unknown code: {code}")
        self._clicks[code] += 1
        self._save()
        return self._urls[code]

    def stats(self, code):
        if code not in self._urls:
            raise KeyError(f"unknown code: {code}")
        return {"url": self._urls[code], "clicks": self._clicks[code]}
