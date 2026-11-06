#!/usr/bin/env python3
"""Cache two Apple restore archives for vphone-cli's firmware preparation."""

import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlsplit
from zipfile import ZipFile


def cache_ipsw(url, cache, kind):
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not host.endswith(".cdn-apple.com"):
        raise ValueError("expected an HTTPS URL on an Apple firmware CDN")
    destination = cache / f"{kind}-{hashlib.sha256(url.encode()).hexdigest()}.ipsw"
    if destination.exists():
        return destination
    with tempfile.TemporaryDirectory(dir=cache) as temp:
        download = Path(temp) / "download.ipsw"
        subprocess.run([
            "curl", "--fail", "--show-error", "--silent", "--location",
            "--proto", "=https", "--proto-redir", "=https",
            "--retry", "2", "--output", str(download), "--", url,
        ], check=True)
        with ZipFile(download) as archive:
            archive.getinfo("BuildManifest.plist")
        download.replace(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iphone-url", required=True)
    parser.add_argument("--cloudos-url", required=True)
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    print(cache_ipsw(args.iphone_url, args.cache, "iphone"))
    print(cache_ipsw(args.cloudos_url, args.cache, "cloudos"))


if __name__ == "__main__":
    main()
