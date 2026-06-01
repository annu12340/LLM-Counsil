"""Tiny CLI wrapper around the Shortener service."""

import sys

from shortener import Shortener

store = Shortener()


def main(argv):
    if len(argv) < 2:
        print("usage: cli.py <shorten URL | resolve CODE | stats CODE>")
        return 1

    command = argv[1]

    if command == "shorten":
        code = store.shorten(argv[2])
        print(f"https://sh.rt/{code}")
    elif command == "resolve":
        print(store.resolve(argv[2]))
    elif command == "stats":
        info = store.stats(argv[2])
        print(f"{info['url']} ({info['clicks']} clicks)")
    else:
        print(f"unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
