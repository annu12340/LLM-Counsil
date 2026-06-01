from shortener import Shortener, decode, encode


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
