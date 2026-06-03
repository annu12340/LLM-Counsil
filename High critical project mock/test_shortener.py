import os
import subprocess
import sys
import tempfile

from shortener import Shortener, decode, encode

CLI = os.path.join(os.path.dirname(__file__), "cli.py")


def _run_cli(workdir, *args):
    return subprocess.run(
        [sys.executable, CLI, *args],
        cwd=workdir,
        capture_output=True,
        text=True,
    )


def test_encode_decode_roundtrip():
    for n in [0, 1, 61, 62, 12345]:
        assert decode(encode(n)) == n


def test_first_code_is_not_zero():
    s = Shortener()
    code = s.shorten("https://example.com")
    assert code == encode(1)


def test_resolve_increments_clicks():
    s = Shortener()
    code = s.shorten("https://example.com")
    s.resolve(code)
    s.resolve(code)
    assert s.stats(code)["clicks"] == 2


def test_unique_codes():
    s = Shortener()
    codes = {s.shorten(f"https://example.com/{i}") for i in range(100)}
    assert len(codes) == 100


def test_persistence_across_instances():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "store.json")
        code = Shortener(path).shorten("https://example.com")
        assert Shortener(path).resolve(code) == "https://example.com"
        assert Shortener(path).stats(code)["clicks"] == 1


def test_cli_resolves_across_invocations():
    with tempfile.TemporaryDirectory() as d:
        assert _run_cli(d, "shorten", "https://example.com").stdout.strip() == "https://sh.rt/1"
        assert _run_cli(d, "resolve", "1").stdout.strip() == "https://example.com"
        assert "1 clicks" in _run_cli(d, "stats", "1").stdout


def test_cli_unknown_code_is_friendly():
    with tempfile.TemporaryDirectory() as d:
        result = _run_cli(d, "resolve", "999")
        assert result.returncode == 1
        assert "unknown code" in result.stdout
        assert "Traceback" not in result.stderr


def test_cli_missing_arg_shows_usage():
    with tempfile.TemporaryDirectory() as d:
        result = _run_cli(d, "shorten")
        assert result.returncode == 1
        assert "usage" in result.stdout
        assert "Traceback" not in result.stderr
