# ffmpeg-utilities

Small Python scripts that wrap `ffmpeg`/`ffprobe` to inspect and normalize
voice-anchor recordings used by a learning app.

The recordings under `audio/` are placeholders captured on a Jabra Evolve 20 MS
+ QuickTime — they're noisy and quiet by design and will be replaced by
studio-quality recordings before any release outside dogfooding.

## Requirements

- `ffmpeg` and `ffprobe` on `PATH` (tested with ffmpeg 8.1)
- Python 3.13 (stdlib only — no `pip install` needed)

A pyenv virtualenv named `ffm-util` is the local convention; any 3.13 interpreter works.

## Tools

### `bin/probe.py` — corpus baseline

Recurse a directory and report duration, sample rate, channels, mean/peak dB,
integrated loudness (LUFS-I), loudness range (LRA), and true peak (dBTP) for
each file, followed by min/max/mean across the corpus.

```
python bin/probe.py audio/nato_phonetic
python bin/probe.py audio/ --json > baseline.json
```

### `bin/normalize.py` — peak / loudnorm normalization

Default mode peak-normalizes each file to a true-peak ceiling (`-1.5 dBTP`) by
applying a single linear gain. Output mirrors the input tree at
`<input>-normalized/`.

```
python bin/normalize.py audio/nato_phonetic
python bin/normalize.py audio/ --dry-run
```

For dynamic loudness targeting (two-pass loudnorm with true-peak limiting):

```
python bin/normalize.py audio/ --limit --target-lufs -18
```

Run `--help` on either script for the full flag list.

## Output convention

Source recordings under `audio/` are treated as truth. Processed output is
written to a sibling `*-normalized/` tree and is gitignored.

## License

GPL-3.0 — see [LICENSE](LICENSE).
