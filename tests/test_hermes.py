"""Tests for Agent Hermes routes."""
import subprocess
import sys

DEVKIT = [sys.executable, "devkit.py"]


def run(*args):
    result = subprocess.run(DEVKIT + list(args), capture_output=True, text=True)
    return result


class TestHermesRouter:
    def test_hermes_no_route_shows_help(self):
        r = run("hermes")
        assert r.returncode != 0
        assert "Available routes (9)" in r.stdout

    def test_hermes_unknown_route(self):
        r = run("hermes", "unknown")
        assert r.returncode != 0


class TestHermesInfo:
    def test_info(self):
        r = run("hermes", "info")
        assert r.returncode == 0
        assert "Hostname:" in r.stdout
        assert "Platform:" in r.stdout
        assert "Python:" in r.stdout


class TestHermesDns:
    def test_dns_lookup(self):
        r = run("hermes", "dns", "example.com")
        assert r.returncode == 0
        assert "DNS lookup: example.com" in r.stdout
        assert "IPv4:" in r.stdout


class TestHermesHttp:
    def test_http_get(self):
        r = run("hermes", "http", "example.com")
        assert r.returncode == 0
        assert "Status:" in r.stdout
        assert "200" in r.stdout

    def test_http_invalid_url(self):
        r = run("hermes", "http", "https://thisdomaindoesnotexist12345.invalid")
        assert r.returncode != 0


class TestHermesHeaders:
    def test_headers(self):
        r = run("hermes", "headers", "example.com")
        assert r.returncode == 0
        assert "Content-Type:" in r.stdout


class TestHermesPort:
    def test_port_check(self):
        r = run("hermes", "port", "example.com", "--ports", "80,443")
        assert r.returncode == 0
        assert "Port scan:" in r.stdout
        assert "OPEN" in r.stdout


class TestHermesIp:
    def test_ip(self):
        r = run("hermes", "ip")
        assert r.returncode == 0
        assert "Local IP:" in r.stdout


class TestHermesPing:
    def test_ping(self):
        r = run("hermes", "ping", "127.0.0.1", "-n", "1")
        assert r.returncode == 0
        assert "1 packets transmitted" in r.stdout or "1 received" in r.stdout
