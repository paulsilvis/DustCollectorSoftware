#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt


# Matches a radon line like:
#     F 108:0 adc_watch - C (11)
RADON_LINE_RE = re.compile(
    r"^\s*(?P<kind>[FCM])\s+"
    r"(?P<line>\d+):(?P<col>\d+)\s+"
    r"(?P<name>.+?)\s+-\s+"
    r"(?P<grade>[A-F])\s+\((?P<cc>\d+)\)\s*$"
)


@dataclass(frozen=True)
class Block:
    file: str
    kind: str  # F, C, M
    name: str
    grade: str
    cc: int
    line: int
    col: int


def _run_radon(root: str) -> str:
    """
    Runs 'radon cc -s -a <root>' and returns stdout.

    Hazard level: low (read-only tool).
    """
    cmd = ["radon", "cc", "-s", "-a", root]
    try:
        proc = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        raise SystemExit("radon not found. Activate venv or 'pip install radon'.")
    except subprocess.CalledProcessError as e:
        msg = (e.stderr or "").strip()
        raise SystemExit(f"radon failed: {msg if msg else e}")
    return proc.stdout


def _parse_radon(text: str) -> List[Block]:
    blocks: List[Block] = []
    cur_file: Optional[str] = None

    for raw in text.splitlines():
        line = raw.rstrip("\n")

        # File header lines look like: "src/main.py"
        # (No leading whitespace in typical radon output.)
        if line and not line.startswith(" ") and line.endswith(".py"):
            cur_file = line.strip()
            continue

        m = RADON_LINE_RE.match(line)
        if not m:
            continue

        if cur_file is None:
            # Unexpected, but don't crash.
            cur_file = "<unknown>"

        blocks.append(
            Block(
                file=cur_file,
                kind=m.group("kind"),
                name=m.group("name").strip(),
                grade=m.group("grade"),
                cc=int(m.group("cc")),
                line=int(m.group("line")),
                col=int(m.group("col")),
            )
        )

    return blocks


def _histogram(values: Iterable[int]) -> Tuple[List[int], List[int]]:
    """
    Returns (xs, counts) where xs are unique complexity values in ascending order.
    """
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    xs = sorted(counts.keys())
    ys = [counts[x] for x in xs]
    return xs, ys


def _integrated_complexity(values: Iterable[int]) -> int:
    return sum(int(v) for v in values)


def _avg(values: List[int]) -> float:
    return (sum(values) / len(values)) if values else 0.0


def _write_csv(blocks: List[Block], path: Path) -> None:
    lines = ["file,kind,name,grade,cc,line,col"]
    for b in blocks:
        # crude CSV escaping: wrap name in quotes and escape quotes
        name = '"' + b.name.replace('"', '""') + '"'
        lines.append(f"{b.file},{b.kind},{name},{b.grade},{b.cc},{b.line},{b.col}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _plot_histogram(
    xs: List[int],
    ys: List[int],
    *,
    title: str,
    out_path: Path,
    blocks_total: int,
    cc_avg: float,
    cc_sum: int,
    cc_max: int,
) -> None:
    plt.figure()
    plt.bar(xs, ys)
    plt.xlabel("Cyclomatic complexity (CC)")
    plt.ylabel("Count (blocks)")
    plt.title(title)

    # Make x ticks readable (only show those that exist)
    plt.xticks(xs)

    footer = (
        f"blocks={blocks_total} | avg={cc_avg:.2f} | "
        f"integrated={cc_sum} | max={cc_max}"
    )
    # place footer under plot
    plt.figtext(0.5, 0.01, footer, ha="center")

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(out_path, dpi=160)
    plt.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Plot radon CC histogram + integrated complexity."
    )
    ap.add_argument(
        "--root",
        default="src",
        help="Directory to analyze (default: src).",
    )
    ap.add_argument(
        "--out",
        default="complexity_hist.png",
        help="Output PNG path (default: complexity_hist.png).",
    )
    ap.add_argument(
        "--title",
        default=None,
        help="Chart title (default: 'Cyclomatic complexity histogram').",
    )
    ap.add_argument(
        "--csv",
        default=None,
        help="Optional: write per-block CSV to this path.",
    )
    ap.add_argument(
        "--stdin",
        action="store_true",
        help="Read radon output from stdin instead of running radon.",
    )

    args = ap.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    else:
        text = _run_radon(args.root)

    blocks = _parse_radon(text)
    if not blocks:
        raise SystemExit(
            "No blocks parsed. Are you sure this is radon 'cc -s -a' output?"
        )

    values = [b.cc for b in blocks]
    xs, ys = _histogram(values)

    cc_sum = _integrated_complexity(values)
    cc_avg = _avg(values)
    cc_max = max(values) if values else 0

    # Console summary (useful even if you never open the PNG)
    print(f"blocks: {len(values)}")
    print(f"avg_cc: {cc_avg:.3f}")
    print(f"integrated_cc: {cc_sum}")
    print(f"max_cc: {cc_max}")
    print(f"hist: {dict(zip(xs, ys))}")

    title = args.title or "Cyclomatic complexity histogram"
    out_path = Path(args.out)

    _plot_histogram(
        xs,
        ys,
        title=title,
        out_path=out_path,
        blocks_total=len(values),
        cc_avg=cc_avg,
        cc_sum=cc_sum,
        cc_max=cc_max,
    )
    print(f"Wrote: {out_path}")

    if args.csv:
        csv_path = Path(args.csv)
        _write_csv(blocks, csv_path)
        print(f"Wrote: {csv_path}")


if __name__ == "__main__":
    main()
