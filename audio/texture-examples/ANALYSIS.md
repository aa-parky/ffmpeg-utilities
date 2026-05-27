# Signal Texture Control Set — Audio Analysis

**Date:** 2025-05-27
**Source:** Copy 653 texture preview engine, seed=42
**Parameters:** 20 WPM character / 10 WPM effective, cadence variation=1, claimed set: K M U R E S N A P T
**Tone frequency:** 700 Hz (default)

## Revision History

| Rev | Date       | Changes |
|-----|------------|---------|
| v1  | 2025-05-27 | Baseline: envelope-only T axis, conservative S curve |
| v2  | 2025-05-27 | Redesign: steeper S curve (×4.4 multiplier), T axis adds harmonic distortion + AC ripple |
| v3  | 2025-05-27 | Constant-loudness normalisation: `gain = 1/sqrt(1 + ratio²)` keeps total power constant across S values |

## Control Set

19 WAV files covering:
- **S sweep** (S1–S9, T=9): isolates noise floor (receiver bed)
- **T sweep** (T1–T9, S=9): isolates tone quality (envelope + distortion + ripple)
- **Combined:** S1/T1, S5/T5

## Strength (S) Sweep — Noise Floor (v2)

T fixed at 9 (clean tone). S controls `receiver_bed` (0–10), dB formula: `-50 + bed × 4.4`.

| File    | S | Bed | RST Description                   | Peak (dB FS) | RMS (dB FS) | Floor (dB FS) | SNR (Peak − Floor) |
|---------|---|-----|-----------------------------------|--------------|-------------|----------------|---------------------|
| S1_T9   | 1 | 10  | Faint signals, barely perceptible | -0.77        | -15.08      | -16.88         | 16.1 dB             |
| S2_T9   | 2 |  9  | Very weak signals                 | -3.89        | -17.78      | -21.27         | 17.4 dB             |
| S3_T9   | 3 |  8  | Weak signals                      | -5.79        | -19.42      | -25.70         | 19.9 dB             |
| S4_T9   | 4 |  6  | Fair signals                      | -8.53        | -20.54      | -34.53         | 26.0 dB             |
| S5_T9   | 5 |  5  | Fairly good signals               | -9.16        | -20.66      | -38.90         | 29.7 dB             |
| S6_T9   | 6 |  4  | Good signals                      | -9.75        | -20.71      | -43.31         | 33.6 dB             |
| S7_T9   | 7 |  2  | Moderately strong signals         | -10.21       | -20.73      | -52.07         | 41.9 dB             |
| S8_T9   | 8 |  1  | Strong signals                    | -10.28       | -20.73      | -56.49         | 46.2 dB             |
| S9_T9   | 9 |  0  | Extremely strong signals          | -10.46       | -20.74      | -279.38        | silence             |

### S-axis observations (v2 vs v1)

- **Total floor range: ~40 dB** (from -16.9 at S1 to -56.5 at S8). Was 13.5 dB in v1.
- **S1 SNR is now 16 dB** (was 36 dB). The signal is audible but the noise is competitive — the learner must concentrate. This is closer to what "barely perceptible" means in practice.
- **S1 peak is -0.8 dB FS** — the noise floor is so high it pushes the combined peak near clipping. The tone at amplitude=0.3 (-10.5 dB FS) is only 16 dB above the floor.
- The progression is now perceptually graduated: S1–S3 are genuinely challenging, S4–S6 are comfortable with noticeable presence, S7–S8 are clean with trace hiss, S9 is silent floor.
- Per-step changes are more even across the middle range (~3–5 dB per step from S2–S7).

## Tone (T) Sweep — Tone Quality (v2)

S fixed at 9 (no noise bed). T now drives three mechanisms: envelope ramp, harmonic distortion (`tanh` soft-clip), and AC ripple (60 Hz AM).

| File    | T | Ramp (ms) | Distortion | Ripple | RST Description                                          | Peak (dB FS) | RMS (dB FS) | Out-of-Band (dB FS) |
|---------|---|-----------|------------|--------|-----------------------------------------------------------|--------------|-------------|----------------------|
| S9_T1   | 1 |  0.0      | 0.80       | 0.70   | Sixty cycle AC or less, very rough and broad               | -10.61       | -22.01      | -24.28               |
| S9_T2   | 2 |  3.0      | 0.72       | 0.56   | Very rough AC, very harsh and broad                        | -10.59       | -21.20      | -23.48               |
| S9_T3   | 3 |  5.0      | 0.64       | 0.42   | Rough AC tone, rectified but not filtered                  | -10.57       | -20.34      | -22.62               |
| S9_T4   | 4 |  8.5      | 0.48       | 0.14   | Rough note, some trace of filtering                        | -10.52       | -18.80      | -21.12               |
| S9_T5   | 5 | 10.0      | 0.40       | 0.00   | Filtered rectified AC but strongly ripple-modulated        | -10.46       | -18.16      | -20.52               |
| S9_T6   | 6 | 11.0      | 0.32       | 0.00   | Filtered tone, definite trace of ripple modulation         | -10.46       | -18.34      | -20.74               |
| S9_T7   | 7 | 13.0      | 0.16       | 0.00   | Near pure tone, trace of ripple modulation                 | -10.46       | -18.96      | -21.49               |
| S9_T8   | 8 | 14.0      | 0.08       | 0.00   | Near perfect tone, slight trace of modulation              | -10.46       | -19.48      | -22.09               |
| S9_T9   | 9 | 15.0      | 0.00       | 0.00   | Perfect tone, no trace of ripple or modulation of any kind | -10.46       | -20.74      | -23.42               |

### T-axis observations (v2 vs v1)

- **Total RMS change: 2.6 dB** (from -22.0 at T1 to -20.7 at T9, noting T1 is quieter due to AM modulation). Was 0.65 dB in v1.
- **Total out-of-band energy change: 3.1 dB** (from -24.3 at T1 to -21.1 at T4 peak, back to -23.4 at T9). Was 0.66 dB in v1.
- **The T axis is now measurably active.** The 3+ dB out-of-band swing crosses the "clearly noticeable" threshold.
- Distortion (harmonic richness) is the dominant effect — it engages across the full T1–T8 range with a smooth taper.
- Ripple (AC hum) engages below T5 and becomes strong at T1–T2, adding the characteristic amplitude flutter of poorly filtered transmitters.
- The RMS curve has an interesting shape: T5 is actually the *loudest* because distortion adds harmonics (energy) while ripple subtracts it (AM troughs). T1 sits 2 dB below T5 due to the deep ripple.
- **Room for improvement:** The distortion and ripple depths could be increased. The current T1 is "rough with hum" but not yet "barely intelligible." More aggressive drive values and deeper ripple modulation would widen the gap further.

## Combined Settings (v2)

| File    | S | T | Bed | Ramp (ms) | Dist | Ripple | Peak (dB FS) | RMS (dB FS) | Floor (dB FS) |
|---------|---|---|-----|-----------|------|--------|--------------|-------------|----------------|
| S1_T1   | 1 | 1 | 10  |  0.0      | 0.80 | 0.70   | -0.91        | -15.40      | -16.88         |
| S5_T5   | 5 | 5 |  5  | 10.0      | 0.40 | 0.00   | -8.95        | -18.12      | -38.90         |
| S9_T9   | 9 | 9 |  0  | 15.0      | 0.00 | 0.00   | -10.46       | -20.74      | -279.38        |

- **S1/T1 is now a genuinely difficult listen.** The signal is distorted, AM-modulated, and sitting 16 dB above a dense noise floor. Copyable with effort — not comfortable.
- **S5/T5 is a noticeably imperfect but comfortable signal.** Moderate distortion harmonics, no ripple, gentle noise floor.
- **S9/T9 is clinically clean** — the heart-monitor baseline.

## Summary — v1 vs v2

| Axis | v1 Mechanism          | v1 Range | v2 Mechanisms                               | v2 Range | Perceptual |
|------|-----------------------|----------|---------------------------------------------|----------|------------|
| S    | Noise floor (×1.5)    | 13.5 dB  | Noise floor (×4.4)                          | ~40 dB   | Dramatic improvement |
| T    | Envelope ramp only    | 0.66 dB  | Envelope ramp + tanh distortion + 60 Hz AM  | ~3.1 dB  | Audible, room to grow |
| S+T  | S dominates           | ~14 dB   | Both axes contribute                        | ~43 dB   | Both matter |

## Loudness Normalisation — v3

### Problem (v2)

The noise floor added energy on top of the signal. Switching from S9 to S1 produced a 5.2 LUFS jump (perceived ~40% louder) with true peak at -0.7 dB FS — a headphone safety concern.

### Solution

Constant-loudness gain: `signal_gain = 1 / sqrt(1 + ratio²)` where `ratio = noise_rms / signal_amplitude`. Applied to the combined signal+floor output. At S9 the gain is ≈1.0 (no effect). At S1 both signal and noise scale down together, preserving the SNR while keeping total power equal to the original signal-only level.

### LUFS Comparison — S Sweep

| File    | S | v2 LUFS | v3 LUFS | v2 True Peak | v3 True Peak |
|---------|---|---------|---------|--------------|--------------|
| S1_T9   | 1 | -13.1   | **-14.1** | -0.7       | **-1.7**     |
| S2_T9   | 2 | -16.5   | **-16.9** | -3.8       | **-4.2**     |
| S3_T9   | 3 | -19.0   | **-19.1** | -5.8       | -5.9         |
| S4_T9   | 4 | -18.4   | -18.4   | -8.4         | -8.4         |
| S5_T9   | 5 | -18.4   | -18.4   | -9.1         | -9.1         |
| S7_T9   | 7 | -18.5   | -18.5   | -10.2        | -10.2        |
| S9_T9   | 9 | -18.4   | -18.4   | -10.5        | -10.5        |

### Assessment

- **S5–S9 are unchanged** — the floor is too quiet to affect the gain calculation.
- **S1 LUFS dropped from -13.1 to -14.1** — still 4.3 LUFS louder than S9 due to broadband noise energy, but no longer a safety shock. The true peak has 1.7 dB of headroom (was 0.7 dB).
- **The 4.3 LUFS residual gap** is inherent: broadband noise contributes more perceived loudness per unit RMS than a narrowband tone. Perfect LUFS matching would require a frequency-weighted normalisation, which would over-attenuate the tone. The current power-matching is a good compromise.
- **SNR is preserved** — S1 still presents a 6 dB signal-to-noise ratio. The challenge is in distinguishing the signal, not in enduring the volume.

### Remaining tuning opportunities

1. **T-axis drive:** `distortion_for_tone_shape` currently peaks at 0.8; pushing to 1.0 with a steeper `tanh` drive would make T1 more dramatic.
2. **T-axis ripple:** Peaks at 0.7 depth; 0.9+ would produce the near-inaudible troughs that characterise truly bad signals.
3. **T-axis engagement curve:** Ripple currently disengages at T5. The RST descriptions mention "trace of ripple modulation" at T6–T7 — a small residual amount there might be worth exploring.
