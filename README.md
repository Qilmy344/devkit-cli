# devkit-cli 🛠️

A fast, zero-dependency Python CLI toolkit for everyday developer tasks.

## Features

- **Hash** — Generate MD5, SHA1, SHA256, SHA512 checksums
- **Encode/Decode** — Base64, URL encoding, HTML entities
- **UUID** — Generate v4 UUIDs (single or batch)
- **JSON** — Pretty-print, minify, validate JSON
- **Timestamp** — Convert between Unix timestamps and human-readable dates
- **Lorem** — Generate placeholder text
- **Password** — Generate secure random passwords
- **Agent Hermes** — Network & messenger toolkit with 9 routes:
  - `ping` — Check if a host is reachable
  - `info` — Show local system & network info
  - `ip` — Show local and public IP addresses
  - `dns` — DNS lookup for a hostname
  - `http` — HTTP GET request with response preview
  - `headers` — Show HTTP response headers
  - `port` — Check if TCP ports are open
  - `speed` — Download speed test
  - `whois` — WHOIS lookup for a domain

## Installation

```bash
pip install devkit-cli
```

Or run directly:
```bash
python devkit.py <command> [args]
```

## Usage

```bash
# Hash a string or file
devkit hash "hello world"
devkit hash --file ./myfile.txt --algo sha256

# Base64 encode/decode
devkit encode base64 "some text"
devkit decode base64 "c29tZSB0ZXh0"

# URL encode/decode
devkit encode url "hello world&foo=bar"

# Generate UUIDs
devkit uuid
devkit uuid --count 5

# JSON operations
devkit json format '{"name":"test","value":42}'
devkit json minify '{"name": "test", "value": 42}'
devkit json validate '{"name":"test"}'

# Timestamp conversion
devkit ts now
devkit ts 1700000000
devkit ts "2024-01-15 12:00:00"

# Generate password
devkit password
devkit password --length 32 --no-symbols

# Lorem ipsum
devkit lorem 3 paragraphs
```

## Agent Hermes

```bash
# Check if a host is reachable
devkit hermes ping google.com

# Show system & network info
devkit hermes info

# Show local and public IP
devkit hermes ip

# DNS lookup
devkit hermes dns example.com

# HTTP GET request
devkit hermes http example.com
devkit hermes http example.com --full

# Show HTTP response headers
devkit hermes headers example.com

# Check TCP ports
devkit hermes port example.com --ports 80,443,8080

# Download speed test
devkit hermes speed
devkit hermes speed --large

# WHOIS lookup
devkit hermes whois example.com
```

## Requirements

Python 3.8+ (no external dependencies)

## License

MIT
