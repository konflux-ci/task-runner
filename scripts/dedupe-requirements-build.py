#!/usr/bin/env python3
"""Keep a single exact pin per package in a pip requirements lockfile.

pybuild-deps compile can emit multiple exact pins for the same package
(e.g. setuptools-scm==10.2.1 and setuptools-scm==7.1.0). Hermetic pip
prefetch cannot resolve that; keep the highest version and merge '# via'
comments onto the surviving block.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path


def parse_blocks(text: str) -> list[str]:
    """Split requirements text into header + package blocks."""
    lines = text.splitlines(keepends=True)
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        if re.match(r"^[A-Za-z0-9_.-]+==", line) and current:
            blocks.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("".join(current))
    return blocks


def pkg_ver(block: str) -> tuple[str, str] | None:
    m = re.match(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)", block)
    if not m:
        return None
    return m.group(1).lower(), m.group(2)


def ver_key(v: str) -> tuple:
    parts = []
    for p in re.split(r"[.-]", v):
        parts.append((0, int(p)) if p.isdigit() else (1, p))
    return tuple(parts)


def merge_via(winner: str, losers: list[str]) -> str:
    via_re = re.compile(r"^[ \t]*# via(?:[ \t]+(.+))?$", re.M)
    extras: list[str] = []
    for block in losers:
        for m in via_re.finditer(block):
            rest = (m.group(1) or "").strip()
            if rest:
                extras.append(rest)
            # following indented via lines
        for line in block.splitlines():
            if re.match(r"^[ \t]*#   \S", line):
                extras.append(line.strip().lstrip("#").strip())

    if not extras:
        return winner

    # Collect existing via entries from winner
    existing: list[str] = []
    lines = winner.splitlines()
    via_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^[ \t]*# via\b", line):
            via_idx = i
            existing_rest = line.split("# via", 1)[1].strip()
            if existing_rest:
                existing.append(existing_rest)
            j = i + 1
            while j < len(lines) and re.match(r"^[ \t]*#   \S", lines[j]):
                existing.append(lines[j].strip().lstrip("#").strip())
                j += 1
            break

    merged = sorted(set(existing + extras), key=str.lower)
    note = (
        "    # note: pybuild-deps may emit multiple pins for this package; "
        "kept the newest for hermetic prefetch."
    )
    via_lines = ["    # via"] + [f"    #   {e}" for e in merged] + [note]

    if via_idx is None:
        # append before trailing blank
        body = winner.rstrip("\n")
        return body + "\n" + "\n".join(via_lines) + "\n"

    # replace via section
    j = via_idx + 1
    while j < len(lines) and (
        re.match(r"^[ \t]*#   \S", lines[j])
        or re.match(r"^[ \t]*# note:", lines[j])
    ):
        j += 1
    new_lines = lines[:via_idx] + via_lines + lines[j:]
    return "\n".join(new_lines) + ("\n" if winner.endswith("\n") else "")


def dedupe(text: str) -> str:
    blocks = parse_blocks(text)
    header: list[str] = []
    by_pkg: dict[str, list[str]] = defaultdict(list)
    order: list[str] = []

    for block in blocks:
        pv = pkg_ver(block)
        if pv is None:
            # preamble / unsafe footer chunks without a leading name==
            if not by_pkg and not order:
                header.append(block)
            else:
                # trailing "unsafe" setuptools block etc. — treat as ordered pkg-less
                order.append(f"__raw__{len(order)}")
                by_pkg[order[-1]].append(block)
            continue
        name, _ = pv
        if name not in by_pkg:
            order.append(name)
        by_pkg[name].append(block)

    out: list[str] = list(header)
    for key in order:
        group = by_pkg[key]
        if key.startswith("__raw__") or len(group) == 1:
            out.extend(group)
            continue
        # keep highest version
        ranked = sorted(
            group,
            key=lambda b: ver_key(pkg_ver(b)[1]),  # type: ignore[index]
            reverse=True,
        )
        out.append(merge_via(ranked[0], ranked[1:]))
    return "".join(out)


def main() -> None:
    path = Path(sys.argv[1])
    original = path.read_text()
    updated = dedupe(original)
    path.write_text(updated)
    # sanity: no duplicate package names with ==
    names = re.findall(r"^([A-Za-z0-9_.-]+)==", updated, re.M)
    dupes = [n for n in set(names) if names.count(n) > 1]
    if dupes:
        raise SystemExit(f"still have duplicate pins: {dupes}")


if __name__ == "__main__":
    main()
