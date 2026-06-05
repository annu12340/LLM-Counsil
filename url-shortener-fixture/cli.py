"""Tiny CLI wrapper around the Shortener service.

State persists in STORE_PATH so codes survive between invocations.
"""

import sys

from shortener import Shortener

STORE_PATH = ".shortener.json"
USAGE = "usage: cli.py <shorten URL | resolve CODE | stats CODE>"


def main(argv):
    if len(argv) < 2 or argv[1] not in ("shorten", "resolve", "stats"):
        print(USAGE)
        return 1

    command = argv[1]
    if len(argv) < 3:
        print(USAGE)
        return 1

    store = Shortener(STORE_PATH)
    arg = argv[2]

    if command == "shorten":
        print(f"https://sh.rt/{store.shorten(arg)}")
        return 0

    try:
        if command == "resolve":
            print(store.resolve(arg))
        else:
            info = store.stats(arg)
            print(f"{info['url']} ({info['clicks']} clicks)")
    except KeyError:
        print(f"unknown code: {arg}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
