#!/usr/bin/env python3
"""Clean the Markdown that fetch_public_pages.py produced from utc.edu.vn.

The lab crawler is deliberately generic: it turns a whole HTML page into text.
On utc.edu.vn that page carries a ~200-line mega-menu, a "latest news" block and,
on some unit pages, a staff roster with personal mobile numbers. DATA_COLLECTION.md
requires the menu and footer to be stripped before the corpus is stored, and
requires that no personal data enters the repo at all.

Three passes, in order:

1. Boilerplate runs. A line that appears on most pages is site chrome - except
   that real section headings ("THONG TIN CHUNG") repeat too. The menu differs by
   arriving in long unbroken runs, so only a run of MIN_RUN or more common lines
   is removed. An isolated repeated heading survives.
2. Tail markers. Everything from the news/"posted by" marker onwards is dropped.
3. Staff rosters. The per-person table is removed and any stray phone number is
   redacted. The unit's own address, switchboard and mailbox are institutional
   contact details and are kept, because a benchmark query may ask for them.

Usage:
    python scripts/clean_utc_pages.py data/dich-vu-sinh-vien-utc
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

# A line must appear on at least this share of the pages to count as chrome.
COMMON_SHARE = 0.6
# ... and chrome is only removed in runs of at least this many lines.
MIN_RUN = 3

# Everything from here down is the site's own furniture, not the page.
TAIL_MARKERS = ("Đăng bởi:", "Bài viết xem nhiều", "Tin tức nổi bật")
# The per-person roster starts at one of these and runs to the end of the body.
# Matching the exact heading is too brittle: the Bao ve page spells it
# "DOI NGU CAN B=O CHUYEN VIEN", with a stray "=" the source site typed. The
# table header "Ho ten" is the reliable anchor - it appears on every roster and
# nowhere in the prose.
ROSTER_PATTERN = re.compile(r"^(ĐỘI NGŨ|DANH SÁCH CÁN BỘ|DANH SÁCH NHÂN SỰ|Họ tên$|Họ và tên$)")

PHONE = re.compile(r"\b0\d[\d\s.\-]{7,12}\d\b")
PERSONAL_EMAIL = re.compile(r"\b[\w.\-]+@utc\.edu\.vn\b")
UNIT_MAILBOXES = {"thuvien@utc.edu.vn", "daotao@utc.edu.vn", "ctsv@utc.edu.vn", "info@utc.edu.vn"}


def split_front_matter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[: end + 4], text[end + 4 :]


def normalise(body: str) -> list[str]:
    # The source pages wrap everything in empty block tags, so the extracted text
    # arrives with runs of hundreds of blank lines.
    #
    # U+00A0 comes from &nbsp; in the source HTML and is invisible in every
    # editor, but it is not a space to anything that compares strings. It broke a
    # benchmark check that looked for "trong va ngoai Truong" in text that reads
    # exactly that way, and it also defeats RecursiveChunker, whose separator list
    # contains a normal space and so cannot split where an NBSP welds two words.
    return [line.strip().replace("﻿", "").replace(" ", " ") for line in body.split("\n")]


def drop_chrome_runs(lines: list[str], common: set[str]) -> list[str]:
    kept: list[str] = []
    index = 0
    while index < len(lines):
        if not lines[index] or lines[index] not in common:
            kept.append(lines[index])
            index += 1
            continue
        run_end = index
        while run_end < len(lines) and lines[run_end] and lines[run_end] in common:
            run_end += 1
        if run_end - index < MIN_RUN:
            kept.extend(lines[index:run_end])
        index = run_end
    return kept


def cut_at(lines: list[str], markers: tuple[str, ...]) -> list[str]:
    for position, line in enumerate(lines):
        if any(line.startswith(marker) for marker in markers):
            return lines[:position]
    return lines


def cut_roster(lines: list[str]) -> list[str]:
    for position, line in enumerate(lines):
        if ROSTER_PATTERN.match(line):
            return lines[:position]
    return lines


def redact(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        emails = PERSONAL_EMAIL.findall(line)
        if any(email.lower() not in UNIT_MAILBOXES for email in emails):
            continue
        cleaned.append(PHONE.sub("[số điện thoại đã lược bỏ]", line) if "ĐT:" in line else line)
    return cleaned


def collapse(lines: list[str]) -> str:
    out: list[str] = []
    for line in lines:
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", type=Path, help="Folder of .md files to clean in place")
    args = parser.parse_args()

    paths = sorted(p for p in args.directory.glob("*.md"))
    if not paths:
        print(f"No .md files in {args.directory}", file=sys.stderr)
        return 2

    documents = {}
    for path in paths:
        front_matter, body = split_front_matter(path.read_text(encoding="utf-8"))
        documents[path] = (front_matter, normalise(body))

    counts = collections.Counter(line for _, lines in documents.values() for line in set(lines) if line)
    threshold = max(2, round(len(documents) * COMMON_SHARE))
    common = {line for line, n in counts.items() if n >= threshold}
    print(f"{len(documents)} documents, {len(common)} candidate boilerplate lines (seen on >= {threshold})")

    for path, (front_matter, lines) in documents.items():
        before = sum(len(line) for line in lines)
        kept = drop_chrome_runs(lines, common)
        kept = cut_at(kept, TAIL_MARKERS)
        kept = cut_roster(kept)
        kept = redact(kept)
        body = collapse(kept)
        path.write_text(f"{front_matter}\n{body}", encoding="utf-8")
        print(f"  {path.name:<32} {before:>6} -> {len(body):>6} chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
