"""Agent Hermes — network & messenger toolkit for devkit-cli.

Hermes is a zero-dependency network agent with 9 built-in routes:
  ping, info, ip, dns, http, headers, port, speed, whois
"""

import json
import os
import platform
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# ─── Router ─────────────────────────────────────────────

class HermesRouter:
    """Route-based dispatcher for Agent Hermes commands."""

    def __init__(self):
        self.routes = {
            "ping": self.route_ping,
            "info": self.route_info,
            "ip": self.route_ip,
            "dns": self.route_dns,
            "http": self.route_http,
            "headers": self.route_headers,
            "port": self.route_port,
            "speed": self.route_speed,
            "whois": self.route_whois,
        }

    def list_routes(self):
        return sorted(self.routes.keys())

    def dispatch(self, route, args):
        handler = self.routes.get(route)
        if handler is None:
            print(
                f"Error: unknown route '{route}'. "
                f"Available: {', '.join(self.list_routes())}",
                file=sys.stderr,
            )
            sys.exit(1)
        handler(args)

    # ── 1. ping ──────────────────────────────────────────

    def route_ping(self, args):
        """Check if a host is reachable."""
        host = args.target
        count = args.count or 4

        flag = "-n" if platform.system().lower() == "windows" else "-c"
        cmd = ["ping", flag, str(count), host]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            print(result.stdout)
            if result.returncode != 0 and result.stderr:
                print(result.stderr, file=sys.stderr)
        except FileNotFoundError:
            print("Error: 'ping' command not found on this system", file=sys.stderr)
            sys.exit(1)
        except subprocess.TimeoutExpired:
            print(f"Error: ping to {host} timed out after 30s", file=sys.stderr)
            sys.exit(1)

    # ── 2. info ──────────────────────────────────────────

    def route_info(self, args):
        """Show local system and network information."""
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            local_ip = "unavailable"

        fqdn = socket.getfqdn()

        print(f"Hostname:    {hostname}")
        print(f"FQDN:        {fqdn}")
        print(f"Local IP:    {local_ip}")
        print(f"Platform:    {platform.system()} {platform.release()}")
        print(f"Machine:     {platform.machine()}")
        print(f"Python:      {platform.python_version()}")
        print(f"Time (UTC):  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")

    # ── 3. ip ────────────────────────────────────────────

    def route_ip(self, args):
        """Show local and public IP addresses."""
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            local_ip = "unavailable"

        print(f"Local IP:   {local_ip}")

        try:
            req = urllib.request.Request(
                "https://api.ipify.org?format=json",
                headers={"User-Agent": "devkit-cli/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                print(f"Public IP:  {data.get('ip', 'unknown')}")
        except Exception:
            print("Public IP:  unavailable (network error)")

    # ── 4. dns ───────────────────────────────────────────

    def route_dns(self, args):
        """Perform DNS lookup for a hostname."""
        host = args.target

        try:
            results = socket.getaddrinfo(host, None)
        except socket.gaierror as e:
            print(f"Error: DNS lookup failed for '{host}' — {e}", file=sys.stderr)
            sys.exit(1)

        seen = set()
        print(f"DNS lookup: {host}\n")
        for family, _, _, _, addr in results:
            ip = addr[0]
            if ip in seen:
                continue
            seen.add(ip)
            family_name = "IPv4" if family == socket.AF_INET else "IPv6"
            print(f"  {family_name}: {ip}")

        try:
            reverse = socket.gethostbyaddr(list(seen)[0])
            print(f"\n  Reverse DNS: {reverse[0]}")
        except (socket.herror, IndexError):
            pass

    # ── 5. http ──────────────────────────────────────────

    def route_http(self, args):
        """Make an HTTP GET request and show the response."""
        url = args.target
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "devkit-cli/1.0"}
            )
            start = time.time()
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed = time.time() - start
                body = resp.read().decode("utf-8", errors="replace")

                print(f"URL:         {url}")
                print(f"Status:      {resp.status} {resp.reason}")
                print(f"Time:        {elapsed:.3f}s")
                print(f"Size:        {len(body)} bytes")
                print(f"Content-Type: {resp.headers.get('Content-Type', 'unknown')}")
                print()

                if args.full:
                    print(body)
                else:
                    preview = body[:500]
                    print(preview)
                    if len(body) > 500:
                        print(f"\n... ({len(body) - 500} more bytes, use --full to see all)")
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} {e.reason}", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"Error: cannot reach '{url}' — {e.reason}", file=sys.stderr)
            sys.exit(1)

    # ── 6. headers ───────────────────────────────────────

    def route_headers(self, args):
        """Show HTTP response headers for a URL."""
        url = args.target
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "devkit-cli/1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"URL:    {url}")
                print(f"Status: {resp.status} {resp.reason}")
                print()
                for key, value in resp.headers.items():
                    print(f"  {key}: {value}")
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} {e.reason}", file=sys.stderr)
            for key, value in e.headers.items():
                print(f"  {key}: {value}")
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"Error: cannot reach '{url}' — {e.reason}", file=sys.stderr)
            sys.exit(1)

    # ── 7. port ──────────────────────────────────────────

    def route_port(self, args):
        """Check if a TCP port is open on a host."""
        host = args.target
        ports_str = args.ports or "80,443"

        try:
            ports = [int(p.strip()) for p in ports_str.split(",")]
        except ValueError:
            print("Error: ports must be comma-separated integers", file=sys.stderr)
            sys.exit(1)

        print(f"Port scan: {host}\n")
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                result = sock.connect_ex((host, port))
                status = "OPEN" if result == 0 else "CLOSED"
                try:
                    service = socket.getservbyport(port, "tcp")
                except OSError:
                    service = "unknown"
                print(f"  :{port:<6} {status:<8} ({service})")
            except socket.gaierror:
                print(f"  :{port:<6} ERROR    (cannot resolve host)")
            except socket.timeout:
                print(f"  :{port:<6} TIMEOUT")
            finally:
                sock.close()

    # ── 8. speed ─────────────────────────────────────────

    def route_speed(self, args):
        """Simple download speed test using a public test file."""
        test_urls = [
            ("1 MB", "https://speed.cloudflare.com/__down?bytes=1000000"),
            ("5 MB", "https://speed.cloudflare.com/__down?bytes=5000000"),
        ]

        label, url = test_urls[0]
        if args.large:
            label, url = test_urls[1]

        print(f"Speed test: downloading {label} file...")
        print()

        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "devkit-cli/1.0"}
            )
            start = time.time()
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            elapsed = time.time() - start

            size_bytes = len(data)
            speed_mbps = (size_bytes * 8) / (elapsed * 1_000_000)
            speed_mbytes = size_bytes / (elapsed * 1_000_000)

            print(f"  Downloaded:  {size_bytes / 1_000_000:.2f} MB")
            print(f"  Time:        {elapsed:.2f}s")
            print(f"  Speed:       {speed_mbps:.2f} Mbps ({speed_mbytes:.2f} MB/s)")
        except Exception as e:
            print(f"Error: speed test failed — {e}", file=sys.stderr)
            sys.exit(1)

    # ── 9. whois ─────────────────────────────────────────

    def route_whois(self, args):
        """Query WHOIS information for a domain."""
        domain = args.target

        domain = re.sub(r"^https?://", "", domain)
        domain = domain.split("/")[0].strip()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect(("whois.iana.org", 43))
            sock.sendall((domain + "\r\n").encode())

            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            sock.close()

            text = response.decode("utf-8", errors="replace")

            refer_match = re.search(r"refer:\s*(\S+)", text)
            if refer_match:
                whois_server = refer_match.group(1)
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock2.settimeout(10)
                sock2.connect((whois_server, 43))
                sock2.sendall((domain + "\r\n").encode())

                response2 = b""
                while True:
                    chunk = sock2.recv(4096)
                    if not chunk:
                        break
                    response2 += chunk
                sock2.close()
                text = response2.decode("utf-8", errors="replace")

            print(f"WHOIS: {domain}\n")
            print(text.strip())

        except socket.gaierror:
            print(f"Error: cannot resolve WHOIS server", file=sys.stderr)
            sys.exit(1)
        except socket.timeout:
            print(f"Error: WHOIS query timed out", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"Error: WHOIS query failed — {e}", file=sys.stderr)
            sys.exit(1)


# ─── CLI Integration ────────────────────────────────────

_router = HermesRouter()


def register_hermes(subparsers):
    """Register the hermes agent subcommand with the main CLI parser."""
    p = subparsers.add_parser(
        "hermes",
        help="Agent Hermes — network & messenger toolkit (9 routes)",
    )
    hsub = p.add_subparsers(dest="route")

    # ping
    p_ping = hsub.add_parser("ping", help="Check if a host is reachable")
    p_ping.add_argument("target", help="Hostname or IP to ping")
    p_ping.add_argument("--count", "-n", type=int, default=4, help="Number of pings")

    # info
    hsub.add_parser("info", help="Show local system & network info")

    # ip
    hsub.add_parser("ip", help="Show local and public IP addresses")

    # dns
    p_dns = hsub.add_parser("dns", help="DNS lookup for a hostname")
    p_dns.add_argument("target", help="Hostname to look up")

    # http
    p_http = hsub.add_parser("http", help="HTTP GET request")
    p_http.add_argument("target", help="URL to fetch")
    p_http.add_argument("--full", action="store_true", help="Show full response body")

    # headers
    p_hdr = hsub.add_parser("headers", help="Show HTTP response headers")
    p_hdr.add_argument("target", help="URL to inspect")

    # port
    p_port = hsub.add_parser("port", help="Check if TCP ports are open")
    p_port.add_argument("target", help="Hostname or IP")
    p_port.add_argument(
        "--ports", "-p", default="80,443", help="Comma-separated ports (default: 80,443)"
    )

    # speed
    p_speed = hsub.add_parser("speed", help="Download speed test")
    p_speed.add_argument("--large", action="store_true", help="Use 5 MB test file")

    # whois
    p_whois = hsub.add_parser("whois", help="WHOIS lookup for a domain")
    p_whois.add_argument("target", help="Domain name to query")

    return p


def run_hermes(args):
    """Entry point called from the main CLI dispatcher."""
    if not args.route:
        print("Agent Hermes — network & messenger toolkit")
        print(f"Available routes ({len(_router.routes)}): {', '.join(_router.list_routes())}")
        print("\nUsage: devkit hermes <route> [args]")
        sys.exit(1)
    _router.dispatch(args.route, args)
