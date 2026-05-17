#!/usr/bin/env python3
"""Normalize audio files under a directory into a mirror tree.

Default mode (peak normalize):
  For each file, measure its true peak, then apply a single linear gain
  so the new peak hits the ceiling (-1.5 dBTP by default). No dynamic
  processing — the waveform is just scaled. Loudness rises uniformly.

  $ python bin/normalize.py audio/

With --limit and --target-lufs (loudnorm):
  Two-pass loudnorm in dynamic mode. Pass 1 measures, pass 2 applies the
  gain plus a true-peak limiter so the LUFS target can be reached even
  when peaks would otherwise clip.

  $ python bin/normalize.py audio/ --limit --target-lufs -18
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".aiff", ".aif", ".ogg", ".opus"}

EBUR_TP = re.compile(r"True peak:\s*\n\s*Peak:\s*(-?\d+(?:\.\d+)?)\s*dBFS")


@dataclass
class Result:
    rel: Path
    input_peak_db: float
    gain_db: float
    norm_type: str  # "peak", "linear", or "dynamic"


def measure_true_peak(path: Path) -> float:
    out = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats",
            "-i", str(path), "-filter:a", "ebur128=peak=true",
            "-f", "null", "-",
        ],
        capture_output=True, text=True, check=True,
    ).stderr
    m = EBUR_TP.search(out)
    if not m:
        raise RuntimeError(f"could not parse true peak for {path}")
    return float(m.group(1))


def extract_loudnorm_json(stderr: str) -> dict:
    idx = stderr.find('"input_i"')
    if idx == -1:
        raise RuntimeError("no loudnorm JSON block in ffmpeg output")
    start = stderr.rfind("{", 0, idx)
    depth = 0
    for i in range(start, len(stderr)):
        if stderr[i] == "{":
            depth += 1
        elif stderr[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(stderr[start : i + 1])
    raise RuntimeError("unclosed loudnorm JSON block")


def measure_loudnorm(path: Path, target_i: float, target_tp: float, lra: float) -> dict:
    af = f"loudnorm=I={target_i}:TP={target_tp}:LRA={lra}:print_format=json"
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats",
            "-i", str(path), "-filter:a", af, "-f", "null", "-",
        ],
        capture_output=True, text=True, check=True,
    )
    return extract_loudnorm_json(proc.stderr)


def normalize_peak(src: Path, dst: Path, ceiling_db: float, dry_run: bool) -> Result:
    peak = measure_true_peak(src)
    gain = ceiling_db - peak
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-nostats", "-y",
                "-i", str(src),
                "-filter:a", f"volume={gain:.3f}dB",
                "-c:a", "pcm_s16le",
                str(dst),
            ],
            capture_output=True, text=True, check=True,
        )
    return Result(rel=dst, input_peak_db=peak, gain_db=gain, norm_type="peak")


def normalize_loudnorm(
    src: Path, dst: Path, target_i: float, ceiling_db: float, lra: float, dry_run: bool
) -> Result:
    measured = measure_loudnorm(src, target_i, ceiling_db, lra)
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        af = (
            f"loudnorm=I={target_i}:TP={ceiling_db}:LRA={lra}"
            f":measured_I={measured['input_i']}"
            f":measured_TP={measured['input_tp']}"
            f":measured_LRA={measured['input_lra']}"
            f":measured_thresh={measured['input_thresh']}"
            f":offset={measured['target_offset']}"
            f":print_format=summary"
        )
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-nostats", "-y",
                "-i", str(src),
                "-filter:a", af,
                "-c:a", "pcm_s16le",
                str(dst),
            ],
            capture_output=True, text=True, check=True,
        )
    return Result(
        rel=dst,
        input_peak_db=float(measured["input_tp"]),
        gain_db=float(measured["target_offset"]),
        norm_type=measured["normalization_type"],
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("directory", type=Path, help="input directory (recursed)")
    ap.add_argument(
        "--output", "-o", type=Path,
        help="output directory (default: <input>-normalized)",
    )
    ap.add_argument(
        "--ceiling", type=float, default=-1.5,
        help="true-peak ceiling in dBFS (default: -1.5)",
    )
    ap.add_argument(
        "--target-lufs", type=float,
        help="target integrated loudness for --limit mode (e.g. -18)",
    )
    ap.add_argument(
        "--limit", action="store_true",
        help="two-pass loudnorm with dynamic limiting (requires --target-lufs)",
    )
    ap.add_argument(
        "--lra", type=float, default=11.0,
        help="loudnorm target LRA (default: 11; only used with --limit)",
    )
    ap.add_argument("--ext", action="append", help="extensions to include (repeatable)")
    ap.add_argument("--dry-run", action="store_true", help="report without writing files")
    args = ap.parse_args()

    if args.limit and args.target_lufs is None:
        ap.error("--limit requires --target-lufs")

    root: Path = args.directory.resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    out_root: Path = (
        args.output.resolve() if args.output
        else root.parent / f"{root.name}-normalized"
    )

    exts = (
        {e if e.startswith(".") else f".{e}" for e in args.ext}
        if args.ext else AUDIO_EXTS
    )

    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in exts)
    if not files:
        print(f"no audio files under {root}", file=sys.stderr)
        return 1

    if args.limit:
        print(
            f"mode: loudnorm  I={args.target_lufs} LUFS  "
            f"TP={args.ceiling} dBTP  LRA={args.lra}",
            file=sys.stderr,
        )
    else:
        print(f"mode: peak  ceiling={args.ceiling} dBTP", file=sys.stderr)
    print(f"writing to {out_root}", file=sys.stderr)

    results: list[Result] = []
    for src in files:
        rel = src.relative_to(root)
        dst = out_root / rel
        print(f"  {rel}", file=sys.stderr)
        try:
            if args.limit:
                r = normalize_loudnorm(
                    src, dst, args.target_lufs, args.ceiling, args.lra, args.dry_run
                )
            else:
                r = normalize_peak(src, dst, args.ceiling, args.dry_run)
        except subprocess.CalledProcessError as e:
            tail = (e.stderr or "").strip().splitlines()
            print(f"    failed: {tail[-1] if tail else e}", file=sys.stderr)
            continue
        results.append(Result(rel=rel, input_peak_db=r.input_peak_db,
                              gain_db=r.gain_db, norm_type=r.norm_type))

    if not results:
        return 1

    print()
    header = f"{'file':<44} {'in peak':>9}  {'gain':>7}  {'type':>8}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{str(r.rel):<44} {r.input_peak_db:>8.1f}  "
            f"{r.gain_db:>+6.2f}  {r.norm_type:>8}"
        )

    if args.dry_run:
        print("\n(dry run — no files written)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
