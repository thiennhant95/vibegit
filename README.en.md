# 🧪 vibegit

**How much of your repo is AI slop?** One command, two seconds, no upload.

`vibegit` reads git history (commit metadata only — **never file contents**, no network) and reports:

- **Slop score 0–100** — higher means more AI-assisted / low-discipline signals
- **AI-assistance estimate** — confirmed (trailers/authors) vs likely (message markers)
- **Top signals**: giant commits, short messages, test deletions, file churn, lockfile-only commits
- **SVG badge** for your README + a one-line `--share` string for social

Zero dependencies. Requires Python 3.8+ and `git`.

```
+-- vibegit ----------------------------------------------------
| repo      my-app (main)
| commits   412
| slop      38/100  Slop
| AI-assist ~41.5%  (confirmed 12.3% / likely 29.2%, high confidence)
+-- top signals ----------------------------------------------
| giant commits    18% (74) -> 4.5 pts
| short messages   22.6% (93) -> 5.7 pts
| test deletions   3 commits -> 12.0 pts
+-- share ----------------------------------------------------
| vibegit · my-app: slop 38/100 (Slop) · AI-assisted ~41.5%
+--------------------------------------------------------------
```

## Why

Vibe coding won. But "how much of this repo was machine-written, and is it sloppy?" has no answer today. `vibegit` answers with data you already have: git history.

It looks at what AI leaves behind: `Co-Authored-By` trailers, AI bot authors, "Generated with …" messages, 600-line commits with no tests, `wip` messages, deleted tests, lockfile-only commits.

## Install

No install needed. Copy `vibegit.py`, or:

```bash
git clone https://github.com/thiennhant95/vibegit && cd vibegit
python3 vibegit.py --help
```

## Usage

```bash
python3 vibegit.py .                          # overview card
python3 vibegit.py . --format md > report.md  # Markdown
python3 vibegit.py . --format json            # JSON
python3 vibegit.py . --badge vibegit.svg      # README badge
python3 vibegit.py . --share                  # one-liner for social
python3 vibegit.py . --since "90 days ago"    # time window
python3 vibegit.py . --max-score 40           # CI gate
```

**Exit codes:** `0` ok · `1` score above `--max-score` · `2` not a git repo / no commits · `4` git error.

## Scoring

| Signal | Max points | Notes |
|---|---|---|
| AI assistance | 30 | `confirmed% + 0.5 × likely%`, capped at 60% |
| Giant commits | 10 | > 400 changed lines |
| Short messages | 10 | subject < 15 chars or `wip/fix/update/...` |
| Test deletions | 20 | commit removes test files without additions |
| File churn | 15 | % of files edited > 5 times |
| Lockfile-only | 15 | commits that only touch lockfiles |

Verdict: `0–14` Clean · `15–34` Mild slop · `35–59` Slop · `60+` Heavy slop.

**Confirmed** = AI-named `Co-Authored-By` / `Assisted-by` / `Generated-by` trailers, AI bot authors, or "Generated with [tool]" messages.
**Likely** = AI tool mentioned in the message/trailer without a hard signal.

The AI number is an **estimate with a confidence band**, not proof of authorship. Repos with <15 commits are flagged low-confidence.

## Badge

```markdown
![vibegit](vibegit.svg)
```

## CI

```yaml
- name: vibegit
  run: python3 vibegit.py . --max-score 40 --format md > vibegit.md
```

See `examples/github-action.yml`.

## Privacy

- Only `git log` / `git rev-parse` (read-only).
- **No file contents**, no secrets, no network, no uploads.
- Never executes repository content.

## Limitations

- Heuristic: AI work with no trailer, bot author, or message marker can be invisible.
- Measures process signals, not correctness.
- Shallow clones (`--depth 1`) only expose the latest commit; use a full clone.
- Churn/lockfile metrics skew high on long-lived repos; use `--since` for fair comparisons.

MIT licensed.
