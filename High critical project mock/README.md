# tiny-shortener

A minimal in-memory URL shortener with base-62 short codes.

## Layout

- `shortener.py` — `encode`/`decode` helpers and the `Shortener` service (shorten, resolve, stats).
- `cli.py` — command-line wrapper: `shorten <url>`, `resolve <code>`, `stats <code>`.
- `test_shortener.py` — pytest suite.

## Usage

```bash
python cli.py shorten https://example.com   # -> https://sh.rt/1
python cli.py resolve 1                      # -> https://example.com
python cli.py stats 1                        # -> https://example.com (1 clicks)
```

## Run tests

```bash
pytest
```

## Notes

- State is in-memory only; it resets every run. The CLI creates a fresh `Shortener`
  on each invocation, so codes do not persist between commands.
