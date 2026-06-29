#!/usr/bin/env python3
"""devkit-cli — A zero-dependency Python CLI toolkit for developer tasks."""

import argparse
import base64
import hashlib
import json
import random
import string
import sys
import uuid
from datetime import datetime, timezone
from urllib.parse import quote, unquote

__version__ = "1.0.0"

# ─── Shared Utilities ───────────────────────────────────

def die(message):
    """Print an error message to stderr and exit with code 1."""
    print(message, file=sys.stderr)
    sys.exit(1)


def get_text_input(args, default=None):
    """Join args.input into a single string, falling back to *default*."""
    if args.input:
        return " ".join(args.input)
    if default is not None:
        return default
    die("Error: no input provided")


def parse_json(text):
    """Parse a JSON string, exiting with an error on failure."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        die(f"Error: invalid JSON — {e}")


def print_timestamp(dt):
    """Print a datetime in the standard ISO + Unix format."""
    print(f"ISO:     {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Unix:    {int(dt.timestamp())}")


# ─── Hash ───────────────────────────────────────────────

def cmd_hash(args):
    algos = {"md5", "sha1", "sha256", "sha512"}
    algo = args.algo.lower()
    if algo not in algos:
        die(f"Error: unsupported algo '{algo}'. Use: {', '.join(sorted(algos))}")

    if args.file:
        h = hashlib.new(algo)
        with open(args.file, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        digest = h.hexdigest()
        print(f"{algo.upper()}: {digest}  ({args.file})")
    else:
        data = get_text_input(args).encode()
        digest = hashlib.new(algo, data).hexdigest()
        print(f"{algo.upper()}: {digest}")

# ─── Encode / Decode ────────────────────────────────────

def cmd_encode(args):
    text = get_text_input(args)
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
        die(f"Error: unknown format '{fmt}'. Use: base64, url, html")

def cmd_decode(args):
    text = get_text_input(args)
    fmt = args.format.lower()

    if fmt == "base64":
        try:
            print(base64.b64decode(text).decode())
        except Exception as e:
            die(f"Error: invalid base64 — {e}")
    elif fmt == "url":
        print(unquote(text))
    elif fmt == "html":
        out = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        out = out.replace("&quot;", '"').replace("&#39;", "'")
        print(out)
    else:
        die(f"Error: unknown format '{fmt}'. Use: base64, url, html")

# ─── UUID ───────────────────────────────────────────────

def cmd_uuid(args):
    count = args.count or 1
    for _ in range(count):
        print(str(uuid.uuid4()))

# ─── JSON ───────────────────────────────────────────────

def cmd_json(args):
    text = get_text_input(args)
    sub = args.subcommand

    if sub == "format":
        obj = parse_json(text)
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    elif sub == "minify":
        obj = parse_json(text)
        print(json.dumps(obj, separators=(",", ":"), ensure_ascii=False))
    elif sub == "validate":
        parse_json(text)
        print("✓ Valid JSON")
    else:
        die(f"Error: unknown json subcommand '{sub}'")

# ─── Timestamp ──────────────────────────────────────────

def cmd_ts(args):
    val = get_text_input(args, default="now")

    if val.lower() == "now":
        print_timestamp(datetime.now(timezone.utc))
        return

    # Try parsing as unix timestamp
    try:
        ts = float(val)
        print_timestamp(datetime.fromtimestamp(ts, tz=timezone.utc))
        return
    except (ValueError, OSError):
        pass

    # Try parsing as date string
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S"):
        try:
            dt = datetime.strptime(val, fmt).replace(tzinfo=timezone.utc)
            print_timestamp(dt)
            return
        except ValueError:
            continue

    die(f"Error: cannot parse '{val}' as timestamp or date")

# ─── Password ───────────────────────────────────────────

def cmd_password(args):
    length = args.length or 16
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
    count = args.count or 1
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
        die(f"Error: unknown unit '{unit}'. Use: words, sentences, paragraphs")

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

    dispatch[args.command](args)

if __name__ == "__main__":
    main()
