"""Basic tests for devkit-cli."""
import subprocess
import sys

DEVKIT = [sys.executable, "devkit.py"]


def run(*args):
    result = subprocess.run(DEVKIT + list(args), capture_output=True, text=True)
    return result


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


class TestEncode:
    def test_base64(self):
        r = run("encode", "base64", "hello world")
        assert r.returncode == 0
        assert "aGVsbG8gd29ybGQ=" in r.stdout

    def test_url_encode(self):
        r = run("encode", "url", "hello world")
        assert r.returncode == 0
        assert "hello%20world" in r.stdout


class TestDecode:
    def test_base64(self):
        r = run("decode", "base64", "aGVsbG8gd29ybGQ=")
        assert r.returncode == 0
        assert "hello world" in r.stdout


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


class TestJson:
    def test_format(self):
        r = run("json", "format", '{"a":1,"b":[2,3]}')
        assert r.returncode == 0
        assert '"a"' in r.stdout

    def test_validate(self):
        r = run("json", "validate", '{"ok":true}')
        assert r.returncode == 0
        assert "Valid" in r.stdout

    def test_validate_invalid(self):
        r = run("json", "validate", "{broken")
        assert r.returncode != 0


class TestTs:
    def test_now(self):
        r = run("ts", "now")
        assert r.returncode == 0
        assert "Unix:" in r.stdout


class TestPassword:
    def test_default(self):
        r = run("password")
        assert r.returncode == 0
        assert len(r.stdout.strip()) == 16

    def test_length(self):
        r = run("password", "-l", "32")
        assert r.returncode == 0
        assert len(r.stdout.strip()) == 32


class TestLorem:
    def test_default(self):
        r = run("lorem")
        assert r.returncode == 0
        assert len(r.stdout.strip()) > 50

    def test_words(self):
        r = run("lorem", "5", "words")
        assert r.returncode == 0
        assert len(r.stdout.strip().split()) == 5
