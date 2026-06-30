#!/usr/bin/env python3
"""Telegram bot for Agent Hermes — network & messenger toolkit.

Zero-dependency Telegram bot using only Python stdlib (urllib).
Exposes all 9 Hermes routes via Telegram commands.
"""

import io
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

BOT_TOKEN = os.environ.get("HERMES_BOT_TOKEN", "")
CASTAI_API_KEY = os.environ.get("CASTAI_API_KEY", "")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
POLL_INTERVAL = 1


# ─── Telegram API helpers ───────────────────────────────

def tg_request(method, data=None):
    url = f"{API_BASE}/{method}"
    if data:
        payload = json.dumps(data).encode()
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
    else:
        req = urllib.request.Request(url)
    timeout = 60 if method == "getUpdates" else 30
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[TG API error] {method}: {e}", file=sys.stderr)
        return None


def send_message(chat_id, text, parse_mode=None):
    if len(text) > 4096:
        text = text[:4090] + "\n..."
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode
    return tg_request("sendMessage", data)


# ─── Hermes route handlers ──────────────────────────────

def handle_ping(args):
    if not args:
        return "Usage: /ping <host> [count]\nExample: /ping google.com 4"
    host = args[0]
    count = int(args[1]) if len(args) > 1 and args[1].isdigit() else 4
    count = min(count, 10)

    flag = "-c"
    cmd = ["ping", flag, str(count), host]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout or result.stderr
        return f"🏓 Ping: {host}\n\n{output.strip()}"
    except FileNotFoundError:
        return "Error: 'ping' command not found"
    except subprocess.TimeoutExpired:
        return f"Error: ping to {host} timed out"


def handle_info(_args):
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        local_ip = "unavailable"
    fqdn = socket.getfqdn()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return (
        f"📋 System Info\n\n"
        f"Hostname:  {hostname}\n"
        f"FQDN:      {fqdn}\n"
        f"Local IP:  {local_ip}\n"
        f"Platform:  {platform.system()} {platform.release()}\n"
        f"Machine:   {platform.machine()}\n"
        f"Python:    {platform.python_version()}\n"
        f"Time:      {now}"
    )


def handle_ip(_args):
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        local_ip = "unavailable"

    lines = [f"🌐 IP Addresses\n\nLocal IP:   {local_ip}"]

    try:
        req = urllib.request.Request(
            "https://api.ipify.org?format=json",
            headers={"User-Agent": "hermes-bot/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            lines.append(f"Public IP:  {data.get('ip', 'unknown')}")
    except Exception:
        lines.append("Public IP:  unavailable")

    return "\n".join(lines)


def handle_dns(args):
    if not args:
        return "Usage: /dns <hostname>\nExample: /dns google.com"
    host = args[0]

    try:
        results = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        return f"Error: DNS lookup failed for '{host}' — {e}"

    seen = set()
    lines = [f"🔍 DNS Lookup: {host}\n"]
    for family, _, _, _, addr in results:
        ip = addr[0]
        if ip in seen:
            continue
        seen.add(ip)
        fam = "IPv4" if family == socket.AF_INET else "IPv6"
        lines.append(f"  {fam}: {ip}")

    try:
        reverse = socket.gethostbyaddr(list(seen)[0])
        lines.append(f"\n  Reverse: {reverse[0]}")
    except (socket.herror, IndexError):
        pass

    return "\n".join(lines)


def handle_http(args):
    if not args:
        return "Usage: /http <url>\nExample: /http example.com"
    url = args[0]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "hermes-bot/1.0"})
        start = time.time()
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed = time.time() - start
            body = resp.read().decode("utf-8", errors="replace")
            return (
                f"🌍 HTTP GET: {url}\n\n"
                f"Status:       {resp.status} {resp.reason}\n"
                f"Time:         {elapsed:.3f}s\n"
                f"Size:         {len(body)} bytes\n"
                f"Content-Type: {resp.headers.get('Content-Type', 'unknown')}\n\n"
                f"{body[:500]}"
                + (f"\n\n... ({len(body) - 500} more bytes)" if len(body) > 500 else "")
            )
    except urllib.error.HTTPError as e:
        return f"HTTP Error: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return f"Error: cannot reach '{url}' — {e.reason}"


def handle_headers(args):
    if not args:
        return "Usage: /headers <url>\nExample: /headers example.com"
    url = args[0]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        req = urllib.request.Request(
            url, method="HEAD", headers={"User-Agent": "hermes-bot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            lines = [f"📨 Headers: {url}\n", f"Status: {resp.status} {resp.reason}\n"]
            for key, value in resp.headers.items():
                lines.append(f"  {key}: {value}")
            return "\n".join(lines)
    except urllib.error.HTTPError as e:
        lines = [f"HTTP Error: {e.code} {e.reason}\n"]
        for key, value in e.headers.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)
    except urllib.error.URLError as e:
        return f"Error: cannot reach '{url}' — {e.reason}"


def handle_port(args):
    if not args:
        return "Usage: /port <host> [ports]\nExample: /port example.com 80,443,8080"
    host = args[0]
    ports_str = args[1] if len(args) > 1 else "80,443"

    try:
        ports = [int(p.strip()) for p in ports_str.split(",")]
    except ValueError:
        return "Error: ports must be comma-separated integers"

    lines = [f"🔌 Port Scan: {host}\n"]
    for port in ports[:20]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            result = sock.connect_ex((host, port))
            status = "OPEN ✅" if result == 0 else "CLOSED ❌"
            try:
                service = socket.getservbyport(port, "tcp")
            except OSError:
                service = "unknown"
            lines.append(f"  :{port:<6} {status} ({service})")
        except socket.gaierror:
            lines.append(f"  :{port:<6} ERROR (cannot resolve)")
        except socket.timeout:
            lines.append(f"  :{port:<6} TIMEOUT")
        finally:
            sock.close()

    return "\n".join(lines)


def handle_speed(_args):
    url = "https://speed.cloudflare.com/__down?bytes=1000000"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "hermes-bot/1.0"})
        start = time.time()
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        elapsed = time.time() - start

        size_bytes = len(data)
        speed_mbps = (size_bytes * 8) / (elapsed * 1_000_000)
        speed_mbytes = size_bytes / (elapsed * 1_000_000)

        return (
            f"⚡ Speed Test\n\n"
            f"Downloaded:  {size_bytes / 1_000_000:.2f} MB\n"
            f"Time:        {elapsed:.2f}s\n"
            f"Speed:       {speed_mbps:.2f} Mbps ({speed_mbytes:.2f} MB/s)"
        )
    except Exception as e:
        return f"Error: speed test failed — {e}"


def handle_whois(args):
    if not args:
        return "Usage: /whois <domain>\nExample: /whois example.com"
    domain = args[0]
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

        output = text.strip()
        if len(output) > 3500:
            output = output[:3500] + "\n\n... (truncated)"

        return f"📝 WHOIS: {domain}\n\n{output}"

    except socket.gaierror:
        return "Error: cannot resolve WHOIS server"
    except socket.timeout:
        return "Error: WHOIS query timed out"
    except OSError as e:
        return f"Error: WHOIS query failed — {e}"


def _cast_api(endpoint):
    """Make a CAST AI API request."""
    url = f"https://api.cast.ai{endpoint}"
    req = urllib.request.Request(
        url, headers={"X-API-Key": CASTAI_API_KEY, "User-Agent": "hermes-bot/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            err = json.loads(body)
            msg = err.get("message", str(e))
        except json.JSONDecodeError:
            msg = str(e)
        return {"error": msg}
    except urllib.error.URLError as e:
        return {"error": f"cannot reach CAST AI API — {e.reason}"}


def handle_cast(args):
    if not CASTAI_API_KEY:
        return "Error: CASTAI_API_KEY not configured on server"

    action = args[0].lower() if args else "help"

    if action == "me":
        data = _cast_api("/v1/me")
        if "error" in data:
            return f"Error: {data['error']}"
        return (
            f"\U0001f464 CAST AI Account\n\n"
            f"ID:       {data.get('id', 'N/A')}\n"
            f"Name:     {data.get('name', 'N/A')}\n"
            f"Email:    {data.get('email', 'N/A')}\n"
            f"Username: {data.get('username', 'N/A')}"
        )

    elif action == "org":
        data = _cast_api("/v1/organizations")
        if "error" in data:
            return f"Error: {data['error']}"
        orgs = data.get("organizations", [])
        lines = [f"\U0001f3e2 CAST AI Organizations ({len(orgs)})\n"]
        for org in orgs:
            lines.append(f"  Name:    {org.get('name') or '(default)'}")
            lines.append(f"  ID:      {org.get('id', 'N/A')}")
            lines.append(f"  Type:    {org.get('type', 'N/A')}")
            lines.append(f"  Created: {org.get('createdAt', 'N/A')}")
            lines.append("")
        return "\n".join(lines)

    elif action == "clusters":
        data = _cast_api("/v1/kubernetes/external-clusters")
        if "error" in data:
            return f"Error: {data['error']}"
        items = data.get("items", [])
        if not items:
            return "\u2601\ufe0f No clusters connected to CAST AI.\nConnect at https://app.kimchi.dev/"
        lines = [f"\u2601\ufe0f CAST AI Clusters ({len(items)})\n"]
        for c in items:
            lines.append(f"  Name:     {c.get('name', 'N/A')}")
            lines.append(f"  ID:       {c.get('id', 'N/A')}")
            lines.append(f"  Provider: {c.get('cloudProvider', 'N/A')}")
            lines.append(f"  Region:   {c.get('region', 'N/A')}")
            lines.append(f"  Status:   {c.get('status', 'N/A')}")
            lines.append("")
        return "\n".join(lines)

    elif action == "tokens":
        data = _cast_api("/v1/auth/tokens")
        if "error" in data:
            return f"Error: {data['error']}"
        items = data.get("items", [])
        lines = [f"\U0001f511 CAST AI API Tokens ({len(items)})\n"]
        for t in items:
            status = "active" if t.get("active") else "inactive"
            ro = " (readonly)" if t.get("readonly") else ""
            lines.append(f"  {t.get('name', 'N/A')} [{t.get('tokenPrefix', '')}...] {status}{ro}")
            lines.append(f"    Last used: {t.get('lastUsedAt', 'never')}")
        return "\n".join(lines)

    else:
        return (
            "\U0001f3af CAST AI — Kubernetes Cost Optimization\n\n"
            "Usage: /cast <action>\n\n"
            "Actions:\n"
            "  me       — Show account info\n"
            "  org      — Show organizations\n"
            "  clusters — List connected clusters\n"
            "  tokens   — List API tokens"
        )


# ─── Command dispatcher ─────────────────────────────────

COMMANDS = {
    "ping": handle_ping,
    "info": handle_info,
    "ip": handle_ip,
    "dns": handle_dns,
    "http": handle_http,
    "headers": handle_headers,
    "port": handle_port,
    "speed": handle_speed,
    "whois": handle_whois,
    "cast": handle_cast,
}

HELP_TEXT = """🛡 *Agent Hermes* — Network & Messenger Toolkit

Available commands (10 routes):

/ping <host> [count] — Check if host is reachable
/info — Show server system info
/ip — Show local & public IP
/dns <hostname> — DNS lookup
/http <url> — HTTP GET request
/headers <url> — Show HTTP response headers
/port <host> [ports] — Check TCP ports (e.g. 80,443)
/speed — Download speed test
/whois <domain> — WHOIS lookup
/cast <action> — CAST AI (me/org/clusters/tokens)

/help — Show this help message
/start — Welcome message"""


def process_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if not text or not text.startswith("/"):
        return

    parts = text.split()
    cmd = parts[0].lower().lstrip("/").split("@")[0]
    args = parts[1:]

    if cmd in ("start", "help"):
        send_message(chat_id, HELP_TEXT, parse_mode="Markdown")
        return

    handler = COMMANDS.get(cmd)
    if handler:
        send_message(chat_id, "⏳ Processing...")
        try:
            result = handler(args)
            send_message(chat_id, result)
        except Exception as e:
            send_message(chat_id, f"Error: {e}")
    else:
        send_message(
            chat_id,
            f"Unknown command: /{cmd}\n\nType /help for available commands.",
        )


# ─── Long-polling loop ──────────────────────────────────

def main():
    if not BOT_TOKEN:
        print("Error: HERMES_BOT_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    me = tg_request("getMe")
    if not me or not me.get("ok"):
        print("Error: invalid bot token or cannot reach Telegram API", file=sys.stderr)
        sys.exit(1)

    bot_name = me["result"].get("username", "unknown")
    print(f"Agent Hermes bot started: @{bot_name}")
    print(f"Routes: {', '.join(sorted(COMMANDS.keys()))}")

    offset = 0
    while True:
        try:
            updates = tg_request(
                "getUpdates",
                {"offset": offset, "timeout": 30, "allowed_updates": ["message"]},
            )
            if updates and updates.get("ok"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        process_message(update["message"])
        except KeyboardInterrupt:
            print("\nBot stopped.")
            break
        except Exception as e:
            print(f"[poll error] {e}", file=sys.stderr)
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
