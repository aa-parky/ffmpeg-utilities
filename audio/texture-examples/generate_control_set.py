"""Generate a control set of texture preview WAVs for analysis.

Produces 20 files:
  - S sweep: S1..S9 with T=9 (isolates noise floor)
  - T sweep: T1..T9 with S=9 (isolates tone shape)
  - Combined: S1/T1 and S5/T5 (extremes and midpoint)

Each file uses the same claimed symbols, seed, and base audio parameters
so the only variable is the texture setting under test.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "malloc-labs-copy" / "src"))

from copy_653.audio import texture
from copy_653.audio.parameters import AudioParameters
from copy_653.audio.wav import encode_pcm16_wav
from copy_653.server.texture_preview_audio import build_texture_preview

OUTPUT_DIR = Path(__file__).resolve().parent
CLAIMED = ("K", "M", "U", "R", "E", "S", "N", "A", "P", "T")
SEED = 42
CHARACTER_WPM = 20
EFFECTIVE_WPM = 10


def make_params(s: int, t: int) -> AudioParameters:
    tone_shape = max(0, min(10, round(((t - 1) * 10) / 8)))
    receiver_bed = max(0, min(10, round(((9 - s) * 10) / 8)))
    return AudioParameters(
        character_speed_wpm=CHARACTER_WPM,
        effective_speed_wpm=EFFECTIVE_WPM,
        envelope_ramp_seconds=texture.envelope_seconds_for_tone_shape(tone_shape),
        tone_distortion=texture.distortion_for_tone_shape(tone_shape),
        tone_ripple=texture.ripple_for_tone_shape(tone_shape),
        receiver_bed=receiver_bed,
        cadence_variation=1,
    )


def generate():
    combos: list[tuple[int, int]] = []

    # S sweep: S1..S9, T fixed at 9
    for s in range(1, 10):
        combos.append((s, 9))

    # T sweep: T1..T9, S fixed at 9
    for t in range(1, 10):
        if (9, t) not in combos:
            combos.append((9, t))

    # Combined corners/midpoint
    for pair in [(1, 1), (5, 5)]:
        if pair not in combos:
            combos.append(pair)

    print(f"Generating {len(combos)} WAV files in {OUTPUT_DIR}\n")

    for s, t in sorted(combos):
        params = make_params(s, t)
        samples = build_texture_preview(params, CLAIMED, seed=SEED)
        wav_bytes = encode_pcm16_wav(samples, params.sample_rate_hz)

        filename = f"S{s}_T{t}.wav"
        path = OUTPUT_DIR / filename
        path.write_bytes(wav_bytes)

        bed = params.receiver_bed
        ramp_ms = params.envelope_ramp_seconds * 1000
        dist = params.tone_distortion
        ripple = params.tone_ripple
        duration_s = len(samples) / params.sample_rate_hz
        size_kb = len(wav_bytes) / 1024

        print(f"  {filename:12s}  bed={bed:2d}  ramp={ramp_ms:5.1f}ms  "
              f"dist={dist:.2f}  ripple={ripple:.2f}  "
              f"dur={duration_s:.1f}s  size={size_kb:.0f}KB")

    print(f"\nDone — {len(combos)} files written.")


if __name__ == "__main__":
    generate()
