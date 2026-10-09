#!/usr/bin/env python3
"""Verify that a deployed readout is anonymously accessible and has the expected title."""

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
MAX_HEAD_BYTES = 512 * 1024


class VerificationError(RuntimeError):
    pass


def extract_title(source: str) -> str:
    match = TITLE_RE.search(source)
    if not match:
        raise VerificationError("document has no <title>")
    return html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()


def expected_title(path: Path) -> str:
    return extract_title(path.read_text(errors="replace"))


def verify(url: str, title: str, timeout: float) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise VerificationError(f"expected an absolute HTTP(S) URL, got {url!r}")
    request = Request(url, headers={"User-Agent": "Warp-Readout-Public-Verification/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            final_url = response.geturl()
            body = response.read(MAX_HEAD_BYTES).decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise VerificationError(f"anonymous request returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise VerificationError(f"anonymous request failed: {exc.reason}") from exc
    if status != 200:
        raise VerificationError(f"anonymous request returned HTTP {status}")
    final_host = (urlparse(final_url).hostname or "").lower()
    if final_host == "vercel.com" or final_host.endswith(".vercel.com"):
        raise VerificationError(f"anonymous request redirected to Vercel authentication: {final_url}")
    remote_title = extract_title(body)
    if remote_title != title:
        raise VerificationError(
            f"remote title mismatch: expected {title!r}, received {remote_title!r}"
        )
    return {
        "url": url,
        "final_url": final_url,
        "status": status,
        "title": remote_title,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="public readout URL")
    expected = parser.add_mutually_exclusive_group(required=True)
    expected.add_argument("--expected-file", type=Path, help="local HTML whose title must match")
    expected.add_argument("--expected-title", help="exact expected HTML title")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--json", action="store_true", help="emit machine-readable verification details")
    args = parser.parse_args()

    if args.expected_file:
        expected_file = args.expected_file.expanduser()
        if not expected_file.is_file():
            raise VerificationError(f"expected HTML file does not exist: {expected_file}")
        title = expected_title(expected_file)
    else:
        title = args.expected_title
    result = verify(args.url, title, args.timeout)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Verified public readout: {result['final_url']} ({result['title']})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except VerificationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
