#!/usr/bin/env python3
"""Prevent common credentials/private keys from being committed accidentally."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {'.git', '_site', '__pycache__', '.venv', 'venv', 'node_modules'}
TEXT_EXTS = {'.py', '.js', '.mjs', '.html', '.css', '.yml', '.yaml', '.json', '.xml', '.txt', '.md', '.toml', '.ini', '.cfg'}

PATTERNS = [
    (re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'), 'private key'),
    (re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b'), 'API key pattern'),
    (re.compile(r'\bghp_[A-Za-z0-9]{30,}\b'), 'GitHub personal access token'),
    (re.compile(r'\bgithub_pat_[A-Za-z0-9_]{40,}\b'), 'GitHub fine-grained token'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'AWS access key'),
    (re.compile(r'(?i)cloudflare[_ -]?(?:api[_ -]?)?token\s*[:=]\s*[\"\']?[A-Za-z0-9_-]{30,}'), 'Cloudflare token'),
]

# Known non-secret/public verification keys may be allowlisted by exact string here.
ALLOW = {
    '6a34c88f59d8939be9f2b8f504a2334c',  # IndexNow public verification key
}


def main() -> int:
    errors=[]
    for path in ROOT.rglob('*'):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        try:
            text=path.read_text(encoding='utf-8')
        except Exception:
            continue
        scan=text
        for allowed in ALLOW:
            scan=scan.replace(allowed, '')
        for pattern,label in PATTERNS:
            if pattern.search(scan):
                errors.append(f'{path.relative_to(ROOT)}: posible {label}')
    if errors:
        print('AUDITORÍA DE SECRETOS: ERROR')
        for item in errors:
            print(' -', item)
        return 2
    print('AUDITORÍA DE SECRETOS: OK')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
