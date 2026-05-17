#!/usr/bin/env python3
"""Probe audio files under a directory and report a level baseline.

For each audio file: duration, sample rate, channels, mean dB, peak dB,
integrated loudness (LUFS-I), loudness range (LRA), and true peak (dBTP).
Prints a per-file table followed by min/max/mean across the corpus.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".aiff", ".aif", ".ogg", ".opus"}

VOLDET_MEAN = re.compile(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB")
VOLDET_PEAK = re.compile(r"max_volume:\s*(-?\d+(?:\.\d+)?)\s*dB")
EBUR_I = re.compile(r"Integrated loudness:\s*\n\s*I:\s*(-?\d+(?:\.\d+)?)\s*LUFS")
EBUR_LRA = re.compile(r"Loudness range:\s*\n\s*LRA:\s*(-?\d+(?:\.\d+)?)\s*LU")
EBUR_TP = re.compile(r"True peak:\s*\n\s*Peak:\s*(-?\d+(?:\.\d+)?)\s*dBFS")


@dataclass
class Probe:
    path: str
    duration: float
    sample_rate: int
    channels: int
    mean_db: float
    peak_db: float
    lufs_i: float
    lra: float
    true_peak_db: float


def _float_or_nan(match: re.Match | None) -> float:
    return float(match.group(1)) if match else math.nan


def ffprobe_meta(path: Path) -> tuple[float, int, int]:
    out = subprocess.run(
        [
            "ffprobe", "-v", "error", "-print_format", "json",
            "-show_streams", "-show_format", str(path),
        ],
        check=True, capture_output=True, text=True,
    ).stdout
    data = json.loads(out)
    stream = next(s for s in data["streams"] if s["codec_type"] == "audio")
    return (
        float(data["format"]["duration"]),
        int(stream["sample_rate"]),
        int(stream["channels"]),
    )


def run_filter(path: Path, afilter: str) -> str:
    return subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats",
            "-i", str(path), "-filter:a", afilter,
            "-f", "null", "-",
        ],
        capture_output=True, text=True, check=True,
    ).stderr


def measure(path: Path) -> Probe:
    duration, sample_rate, channels = ffprobe_meta(path)
    vd = run_filter(path, "volumedetect")
    eb = run_filter(path, "ebur128=peak=true")
    return Probe(
        path=str(path),
        duration=duration,
        sample_rate=sample_rate,
        channels=channels,
        mean_db=_float_or_nan(VOLDET_MEAN.search(vd)),
        peak_db=_float_or_nan(VOLDET_PEAK.search(vd)),
        lufs_i=_float_or_nan(EBUR_I.search(eb)),
        lra=_float_or_nan(EBUR_LRA.search(eb)),
        true_peak_db=_float_or_nan(EBUR_TP.search(eb)),
    )


def find_audio(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.suffix.lower() in AUDIO_EXTS)


def stats(values: list[float]) -> tuple[float, float, float]:
    clean = [v for v in values if not math.isnan(v)]
    if not clean:
        return (math.nan, math.nan, math.nan)
    return (min(clean), max(clean), sum(clean) / len(clean))


def print_table(probes: list[Probe], root: Path) -> None:
    header = (
        f"{'file':<44} {'dur(s)':>7}  {'sr':>5}  {'ch':>2}  "
        f"{'mean dB':>8}  {'peak dB':>8}  {'LUFS-I':>7}  "
        f"{'LRA':>5}  {'TP dB':>7}"
    )
    print(header)
    print("-" * len(header))
    for p in probes:
        rel = Path(p.path).relative_to(root)
        print(
            f"{str(rel):<44} {p.duration:>7.2f}  {p.sample_rate:>5}  "
            f"{p.channels:>2}  {p.mean_db:>8.1f}  {p.peak_db:>8.1f}  "
            f"{p.lufs_i:>7.1f}  {p.lra:>5.1f}  {p.true_peak_db:>7.1f}"
        )

    print()
    print(f"baseline across {len(probes)} file(s) — min / max / mean:")
    metrics = [
        ("duration (s)", [p.duration for p in probes]),
        ("mean dB     ", [p.mean_db for p in probes]),
        ("peak dB     ", [p.peak_db for p in probes]),
        ("LUFS-I      ", [p.lufs_i for p in probes]),
        ("LRA (LU)    ", [p.lra for p in probes]),
        ("true peak dB", [p.true_peak_db for p in probes]),
    ]
    for label, values in metrics:
        lo, hi, mean = stats(values)
        print(f"  {label}  {lo:>9.2f}  {hi:>9.2f}  {mean:>9.2f}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", type=Path, help="directory to recurse")
    ap.add_argument(
        "--ext", action="append",
        help="audio extension to include (repeatable); default covers common types",
    )
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    root: Path = args.directory.resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    if args.ext:
        exts = {e if e.startswith(".") else f".{e}" for e in args.ext}
    else:
        exts = AUDIO_EXTS

    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in exts)
    if not files:
        print(f"no audio files under {root}", file=sys.stderr)
        return 1

    probes: list[Probe] = []
    for f in files:
        print(f"probing {f.relative_to(root)}", file=sys.stderr)
        probes.append(measure(f))

    if args.json:
        json.dump([asdict(p) for p in probes], sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print_table(probes, root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
