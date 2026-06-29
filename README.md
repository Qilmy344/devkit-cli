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

## Requirements

Python 3.8+ (no external dependencies)

## License

MIT
