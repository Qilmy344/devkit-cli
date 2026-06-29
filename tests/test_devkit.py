"""Comprehensive tests for devkit-cli."""
import subprocess
import sys
import tempfile
import hashlib
import os

DEVKIT = [sys.executable, "devkit.py"]


def run(*args):
    result = subprocess.run(DEVKIT + list(args), capture_output=True, text=True)
    return result


# ─── Hash ────────────────────────────────────────────────


class TestHash:
    def test_sha256(self):
        r = run("hash", "hello")
        assert r.returncode == 0
        assert "SHA256:" in r.stdout
        assert "2cf24dba" in r.stdout

    def test_md5(self):
        r = run("hash", "--algo", "md5", "test")
        assert r.returncode == 0
        assert "MD5:" in r.stdout

    def test_sha1(self):
        r = run("hash", "--algo", "sha1", "hello")
        assert r.returncode == 0
        assert "SHA1:" in r.stdout
        expected = hashlib.sha1(b"hello").hexdigest()
        assert expected in r.stdout

    def test_sha512(self):
        r = run("hash", "--algo", "sha512", "hello")
        assert r.returncode == 0
        assert "SHA512:" in r.stdout
        expected = hashlib.sha512(b"hello").hexdigest()
        assert expected in r.stdout

    def test_file_hashing(self):
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write(b"file content for hashing")
            tmp_path = f.name
        try:
            r = run("hash", "--file", tmp_path, "--algo", "sha256")
            assert r.returncode == 0
            assert "SHA256:" in r.stdout
            expected = hashlib.sha256(b"file content for hashing").hexdigest()
            assert expected in r.stdout
            assert tmp_path in r.stdout
        finally:
            os.unlink(tmp_path)

    def test_file_hashing_md5(self):
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02\xff")
            tmp_path = f.name
        try:
            r = run("hash", "--file", tmp_path, "--algo", "md5")
            assert r.returncode == 0
            expected = hashlib.md5(b"\x00\x01\x02\xff").hexdigest()
            assert expected in r.stdout
        finally:
            os.unlink(tmp_path)

    def test_unsupported_algo(self):
        r = run("hash", "--algo", "crc32", "hello")
        assert r.returncode != 0
        assert "unsupported algo" in r.stderr.lower() or "Error" in r.stderr

    def test_multi_word_input(self):
        r = run("hash", "hello", "world")
        assert r.returncode == 0
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert expected in r.stdout


# ─── Encode ──────────────────────────────────────────────


class TestEncode:
    def test_base64(self):
        r = run("encode", "base64", "hello world")
        assert r.returncode == 0
        assert "aGVsbG8gd29ybGQ=" in r.stdout

    def test_url_encode(self):
        r = run("encode", "url", "hello world")
        assert r.returncode == 0
        assert "hello%20world" in r.stdout

    def test_html_encode(self):
        r = run("encode", "html", "<div>\"test\" & 'value'</div>")
        assert r.returncode == 0
        assert "&lt;" in r.stdout
        assert "&gt;" in r.stdout
        assert "&amp;" in r.stdout
        assert "&quot;" in r.stdout
        assert "&#39;" in r.stdout

    def test_url_encode_special_chars(self):
        r = run("encode", "url", "foo=bar&baz=qux")
        assert r.returncode == 0
        assert "foo%3Dbar%26baz%3Dqux" in r.stdout

    def test_base64_empty_like(self):
        r = run("encode", "base64", "a")
        assert r.returncode == 0
        assert "YQ==" in r.stdout


# ─── Decode ──────────────────────────────────────────────


class TestDecode:
    def test_base64(self):
        r = run("decode", "base64", "aGVsbG8gd29ybGQ=")
        assert r.returncode == 0
        assert "hello world" in r.stdout

    def test_url_decode(self):
        r = run("decode", "url", "hello%20world%26foo%3Dbar")
        assert r.returncode == 0
        assert "hello world&foo=bar" in r.stdout

    def test_html_decode(self):
        r = run("decode", "html", "&lt;div&gt;&quot;test&quot; &amp; &#39;val&#39;&lt;/div&gt;")
        assert r.returncode == 0
        assert '<div>"test" & \'val\'</div>' in r.stdout

    def test_base64_invalid(self):
        r = run("decode", "base64", "!!!not-valid-base64!!!")
        assert r.returncode != 0
        assert "Error" in r.stderr or "invalid" in r.stderr.lower()

    def test_base64_roundtrip(self):
        r_enc = run("encode", "base64", "roundtrip test")
        encoded = r_enc.stdout.strip()
        r_dec = run("decode", "base64", encoded)
        assert r_dec.returncode == 0
        assert "roundtrip test" in r_dec.stdout


# ─── UUID ────────────────────────────────────────────────


class TestUuid:
    def test_single(self):
        r = run("uuid")
        assert r.returncode == 0
        assert len(r.stdout.strip()) == 36

    def test_batch(self):
        r = run("uuid", "-n", "3")
        assert r.returncode == 0
        lines = [l for l in r.stdout.strip().splitlines() if l]
        assert len(lines) == 3

    def test_uuid_format(self):
        r = run("uuid")
        assert r.returncode == 0
        parts = r.stdout.strip().split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_batch_unique(self):
        r = run("uuid", "-n", "5")
        assert r.returncode == 0
        lines = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
        assert len(lines) == len(set(lines))


# ─── JSON ────────────────────────────────────────────────


class TestJson:
    def test_format(self):
        r = run("json", "format", '{"a":1,"b":[2,3]}')
        assert r.returncode == 0
        assert '"a"' in r.stdout

    def test_format_pretty_output(self):
        r = run("json", "format", '{"name":"test","value":42}')
        assert r.returncode == 0
        assert "\n" in r.stdout
        assert "  " in r.stdout

    def test_format_invalid_json(self):
        r = run("json", "format", "{broken json")
        assert r.returncode != 0
        assert "Error" in r.stderr or "invalid" in r.stderr.lower()

    def test_minify(self):
        r = run("json", "minify", '{"name": "test", "value": 42}')
        assert r.returncode == 0
        output = r.stdout.strip()
        assert " " not in output or output == '{"name":"test","value":42}'
        assert '"name":"test"' in output
        assert '"value":42' in output

    def test_minify_invalid_json(self):
        r = run("json", "minify", "not json at all")
        assert r.returncode != 0
        assert "Error" in r.stderr or "invalid" in r.stderr.lower()

    def test_validate(self):
        r = run("json", "validate", '{"ok":true}')
        assert r.returncode == 0
        assert "Valid" in r.stdout

    def test_validate_invalid(self):
        r = run("json", "validate", "{broken")
        assert r.returncode != 0

    def test_validate_array(self):
        r = run("json", "validate", '[1, 2, 3]')
        assert r.returncode == 0
        assert "Valid" in r.stdout

    def test_format_unicode(self):
        r = run("json", "format", '{"emoji": "\\u2764"}')
        assert r.returncode == 0
        assert "❤" in r.stdout


# ─── Timestamp ───────────────────────────────────────────


class TestTs:
    def test_now(self):
        r = run("ts", "now")
        assert r.returncode == 0
        assert "Unix:" in r.stdout

    def test_now_has_iso(self):
        r = run("ts", "now")
        assert r.returncode == 0
        assert "ISO:" in r.stdout
        assert "UTC" in r.stdout

    def test_unix_timestamp(self):
        r = run("ts", "1700000000")
        assert r.returncode == 0
        assert "2023-11-14" in r.stdout
        assert "Unix:" in r.stdout
        assert "1700000000" in r.stdout

    def test_unix_timestamp_zero(self):
        r = run("ts", "0")
        assert r.returncode == 0
        assert "1970-01-01" in r.stdout

    def test_date_string_ymd_hms(self):
        r = run("ts", "2024-01-15 12:00:00")
        assert r.returncode == 0
        assert "2024-01-15 12:00:00 UTC" in r.stdout
        assert "Unix:" in r.stdout

    def test_date_string_iso_t(self):
        r = run("ts", "2024-06-01T08:30:00")
        assert r.returncode == 0
        assert "2024-06-01 08:30:00 UTC" in r.stdout

    def test_date_string_ymd_only(self):
        r = run("ts", "2024-01-15")
        assert r.returncode == 0
        assert "2024-01-15 00:00:00 UTC" in r.stdout

    def test_date_string_dmy(self):
        r = run("ts", "15/01/2024 12:00:00")
        assert r.returncode == 0
        assert "2024-01-15 12:00:00 UTC" in r.stdout

    def test_invalid_input(self):
        r = run("ts", "not-a-date")
        assert r.returncode != 0
        assert "Error" in r.stderr or "cannot parse" in r.stderr

    def test_no_args_defaults_to_now(self):
        r = run("ts")
        assert r.returncode == 0
        assert "ISO:" in r.stdout
        assert "Unix:" in r.stdout


# ─── Password ───────────────────────────────────────────


class TestPassword:
    def test_default(self):
        r = run("password")
        assert r.returncode == 0
        assert len(r.stdout.strip()) == 16

    def test_length(self):
        r = run("password", "-l", "32")
        assert r.returncode == 0
        assert len(r.stdout.strip()) == 32

    def test_no_symbols(self):
        r = run("password", "--no-symbols", "-l", "100")
        assert r.returncode == 0
        pw = r.stdout.strip()
        assert len(pw) == 100
        assert pw.isalnum()

    def test_with_symbols(self):
        # Generate many passwords; at least one should contain a symbol
        has_symbol = False
        for _ in range(20):
            r = run("password", "-l", "50")
            assert r.returncode == 0
            pw = r.stdout.strip()
            if not pw.isalnum():
                has_symbol = True
                break
        assert has_symbol, "Expected at least one password with symbols over 20 tries"

    def test_short_password(self):
        r = run("password", "-l", "1")
        assert r.returncode == 0
        assert len(r.stdout.strip()) == 1


# ─── Lorem Ipsum ────────────────────────────────────────


class TestLorem:
    def test_default(self):
        r = run("lorem")
        assert r.returncode == 0
        assert len(r.stdout.strip()) > 50

    def test_words(self):
        r = run("lorem", "5", "words")
        assert r.returncode == 0
        assert len(r.stdout.strip().split()) == 5

    def test_sentences(self):
        r = run("lorem", "3", "sentences")
        assert r.returncode == 0
        text = r.stdout.strip()
        assert text.count(".") >= 3

    def test_single_sentence(self):
        r = run("lorem", "1", "sentence")
        assert r.returncode == 0
        text = r.stdout.strip()
        assert text.endswith(".")
        assert text[0].isupper()

    def test_multiple_paragraphs(self):
        r = run("lorem", "3", "paragraphs")
        assert r.returncode == 0
        paragraphs = r.stdout.strip().split("\n\n")
        assert len(paragraphs) == 3

    def test_single_word(self):
        r = run("lorem", "1", "word")
        assert r.returncode == 0
        words = r.stdout.strip().split()
        assert len(words) == 1

    def test_unknown_unit(self):
        r = run("lorem", "1", "chapters")
        assert r.returncode != 0
        assert "Error" in r.stderr or "unknown unit" in r.stderr.lower()


# ─── Main / CLI ─────────────────────────────────────────


class TestMain:
    def test_no_command_shows_help(self):
        r = run()
        assert r.returncode != 0

    def test_version(self):
        r = run("--version")
        assert r.returncode == 0
        assert "devkit" in r.stdout.lower() or "1.0.0" in r.stdout
