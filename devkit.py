#!/usr/bin/env python3
"""devkit-cli — A zero-dependency Python CLI toolkit for developer tasks."""

import argparse
import base64
import hashlib
import json
import os
import random
import string
import sys
import uuid
from datetime import datetime, timezone
from urllib.parse import quote, unquote

__version__ = "1.0.0"

# ─── Hash ───────────────────────────────────────────────

def cmd_hash(args):
    algos = {"md5", "sha1", "sha256", "sha512"}
    algo = args.algo.lower()
    if algo not in algos:
        print(f"Error: unsupported algo '{algo}'. Use: {', '.join(sorted(algos))}", file=sys.stderr)
        sys.exit(1)

    if args.file:
        h = hashlib.new(algo)
        try:
            with open(args.file, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
        except FileNotFoundError:
            print(f"Error: file not found — {args.file}", file=sys.stderr)
            sys.exit(1)
        except PermissionError:
            print(f"Error: permission denied — {args.file}", file=sys.stderr)
            sys.exit(1)
        except IsADirectoryError:
            print(f"Error: is a directory — {args.file}", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"Error: cannot read file — {e}", file=sys.stderr)
            sys.exit(1)
        digest = h.hexdigest()
        print(f"{algo.upper()}: {digest}  ({args.file})")
    elif not args.input:
        print("Error: provide a string to hash or use --file", file=sys.stderr)
        sys.exit(1)
    else:
        data = " ".join(args.input).encode()
        digest = hashlib.new(algo, data).hexdigest()
        print(f"{algo.upper()}: {digest}")

# ─── Encode / Decode ────────────────────────────────────

def cmd_encode(args):
    text = " ".join(args.input)
    fmt = args.format.lower()

    if fmt == "base64":
        print(base64.b64encode(text.encode()).decode())
    elif fmt == "url":
        print(quote(text, safe=""))
    elif fmt == "html":
        out = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        out = out.replace('"', "&quot;").replace("'", "&#39;")
        print(out)
    else:
        print(f"Error: unknown format '{fmt}'. Use: base64, url, html", file=sys.stderr)
        sys.exit(1)

def cmd_decode(args):
    text = " ".join(args.input)
    fmt = args.format.lower()

    if fmt == "base64":
        try:
            print(base64.b64decode(text).decode())
        except Exception as e:
            print(f"Error: invalid base64 — {e}", file=sys.stderr)
            sys.exit(1)
    elif fmt == "url":
        print(unquote(text))
    elif fmt == "html":
        out = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        out = out.replace("&quot;", '"').replace("&#39;", "'")
        print(out)
    else:
        print(f"Error: unknown format '{fmt}'. Use: base64, url, html", file=sys.stderr)
        sys.exit(1)

# ─── UUID ───────────────────────────────────────────────

def cmd_uuid(args):
    count = args.count if args.count is not None else 1
    if count < 1:
        print("Error: count must be at least 1", file=sys.stderr)
        sys.exit(1)
    for _ in range(count):
        print(str(uuid.uuid4()))

# ─── JSON ───────────────────────────────────────────────

def cmd_json(args):
    text = " ".join(args.input)
    sub = args.subcommand

    if sub == "format":
        try:
            obj = json.loads(text)
            print(json.dumps(obj, indent=2, ensure_ascii=False))
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON — {e}", file=sys.stderr)
            sys.exit(1)

    elif sub == "minify":
        try:
            obj = json.loads(text)
            print(json.dumps(obj, separators=(",", ":"), ensure_ascii=False))
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON — {e}", file=sys.stderr)
            sys.exit(1)

    elif sub == "validate":
        try:
            json.loads(text)
            print("✓ Valid JSON")
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON — {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Error: unknown json subcommand '{sub}'", file=sys.stderr)
        sys.exit(1)

# ─── Timestamp ──────────────────────────────────────────

def cmd_ts(args):
    val = " ".join(args.input) if args.input else "now"

    if val.lower() == "now":
        now = datetime.now(timezone.utc)
        print(f"ISO:     {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Unix:    {int(now.timestamp())}")
        return

    # Try parsing as unix timestamp
    try:
        ts = float(val)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        print(f"ISO:     {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Unix:    {int(ts)}")
        return
    except (ValueError, OSError):
        pass

    # Try parsing as date string
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S"):
        try:
            dt = datetime.strptime(val, fmt).replace(tzinfo=timezone.utc)
            print(f"ISO:     {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"Unix:    {int(dt.timestamp())}")
            return
        except ValueError:
            continue

    print(f"Error: cannot parse '{val}' as timestamp or date", file=sys.stderr)
    sys.exit(1)

# ─── Password ───────────────────────────────────────────

def cmd_password(args):
    length = args.length
    if length < 1:
        print("Error: password length must be at least 1", file=sys.stderr)
        sys.exit(1)
    chars = string.ascii_letters + string.digits
    if not args.no_symbols:
        chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"

    pw = "".join(random.SystemRandom().choice(chars) for _ in range(length))
    print(pw)

# ─── Lorem Ipsum ────────────────────────────────────────

LOREM_WORDS = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua enim ad minim veniam quis nostrud "
    "exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute irure "
    "in reprehenderit voluptate velit esse cillum fugiat nulla pariatur excepteur sint "
    "occaecat cupidatat non proident sunt culpa qui officia deserunt mollit anim id est "
    "laborum perspiciatis unde omnis iste natus error voluptatem accusantium doloremque "
    "laudantium totam rem aperiam eaque ipsa quae ab illo inventore veritatis quasi "
    "architecto beatae vitae dicta explicabo nemo ipsam quia voluptas aspernatur aut "
    "odit fugit consequuntur magni dolores eos ratione sequi nesciunt neque porro quisquam"
).split()

def cmd_lorem(args):
    count = args.count if args.count is not None else 1
    if count < 1:
        print("Error: count must be at least 1", file=sys.stderr)
        sys.exit(1)
    unit = (args.unit or "paragraphs").lower()

    sentences_per_para = 5
    words_per_sentence = 12

    def make_sentence():
        n = random.randint(words_per_sentence - 3, words_per_sentence + 3)
        words = [random.choice(LOREM_WORDS) for _ in range(n)]
        words[0] = words[0].capitalize()
        return " ".join(words) + "."

    if unit in ("words", "word"):
        words = [random.choice(LOREM_WORDS) for _ in range(count)]
        print(" ".join(words))
    elif unit in ("sentences", "sentence"):
        print(" ".join(make_sentence() for _ in range(count)))
    elif unit in ("paragraphs", "paragraph"):
        paras = []
        for _ in range(count):
            paras.append(" ".join(make_sentence() for _ in range(sentences_per_para)))
        print("\n\n".join(paras))
    else:
        print(f"Error: unknown unit '{unit}'. Use: words, sentences, paragraphs", file=sys.stderr)
        sys.exit(1)

# ─── Main ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="devkit", description="🛠️ devkit-cli — developer toolkit")
    parser.add_argument("--version", action="version", version=f"devkit {__version__}")
    sub = parser.add_subparsers(dest="command")

    # hash
    p_hash = sub.add_parser("hash", help="Generate hash (MD5, SHA1, SHA256, SHA512)")
    p_hash.add_argument("input", nargs="*", default=[], help="String to hash")
    p_hash.add_argument("--file", "-f", help="Hash file contents instead")
    p_hash.add_argument("--algo", "-a", default="sha256", help="Algorithm (default: sha256)")

    # encode
    p_enc = sub.add_parser("encode", help="Encode text (base64, url, html)")
    p_enc.add_argument("format", choices=["base64", "url", "html"])
    p_enc.add_argument("input", nargs="+")

    # decode
    p_dec = sub.add_parser("decode", help="Decode text (base64, url, html)")
    p_dec.add_argument("format", choices=["base64", "url", "html"])
    p_dec.add_argument("input", nargs="+")

    # uuid
    p_uuid = sub.add_parser("uuid", help="Generate UUID v4")
    p_uuid.add_argument("--count", "-n", type=int, help="Number of UUIDs")

    # json
    p_json = sub.add_parser("json", help="JSON operations (format, minify, validate)")
    p_json.add_argument("subcommand", choices=["format", "minify", "validate"])
    p_json.add_argument("input", nargs="+")

    # ts
    p_ts = sub.add_parser("ts", help="Timestamp conversion")
    p_ts.add_argument("input", nargs="*", default=["now"])

    # password
    p_pw = sub.add_parser("password", help="Generate secure password")
    p_pw.add_argument("--length", "-l", type=int, default=16)
    p_pw.add_argument("--no-symbols", action="store_true")

    # lorem
    p_lorem = sub.add_parser("lorem", help="Generate placeholder text")
    p_lorem.add_argument("count", nargs="?", type=int, default=1)
    p_lorem.add_argument("unit", nargs="?", default="paragraphs")

    args = parser.parse_args()

    dispatch = {
        "hash": cmd_hash,
        "encode": cmd_encode,
        "decode": cmd_decode,
        "uuid": cmd_uuid,
        "json": cmd_json,
        "ts": cmd_ts,
        "password": cmd_password,
        "lorem": cmd_lorem,
    }

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = dispatch.get(args.command)
    if handler is None:
        print(f"Error: unknown command '{args.command}'", file=sys.stderr)
        sys.exit(1)

    handler(args)


def _cli():
    try:
        main()
    except BrokenPipeError:
        # Silently handle broken pipe (e.g. piping to `head`)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(0)
    except KeyboardInterrupt:
        print("", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    _cli()
