# Ticket: Add a command-line interface (CLI)

**Type:** Feature
**Priority:** Medium
**Component:** Packaging / UX
**Status:** Draft (not yet in Linear)

---

## Summary

Add a `extended-wer-normalizer` console script so transcripts can be normalized
from the shell — no Python required. Today the package is library-only; every
ad-hoc check ("how does the pipeline mangle *this* string?") costs a Python
REPL session, and non-developers (QA, linguists, data annotators) cannot run
the normalizer at all.

Gladia's `gladia-normalization` ships exactly this and it is the right shape:
positional text, `--file`, stdin piping, `--language`, `--describe`.

## Motivation

- **Debugging eval mismatches:** when a WER number looks wrong, the first
  question is "what did the normalizer do to this pair?". A one-liner beats a
  REPL round-trip and works in CI logs, Slack snippets, and bug reports.
- **Pipeline integration:** benchmark scripts in other languages (bash, Rust,
  Node) can pipe transcripts through stdin/stdout instead of shelling out to a
  Python `-c` snippet.
- **Non-developer access:** annotators and QA can verify expected
  normalizations directly, e.g. before adding a test case.
- **Parity with the reference implementation:** `gladia-normalization "text"
  --language en` is the documented entry point of the library we benchmark
  against; matching it removes friction when comparing outputs side by side.

## Proposed interface

```bash
# Positional text (single quotes, so the shell doesn't expand "$5")
extended-wer-normalizer 'Call 0176 or email info@example.com, it costs $5.99'
# → call 0 1 7 6 or email info at example dot com it costs five dollars ninety nine cents

# Language selection (default: en)
extended-wer-normalizer "Hr. Müller, am 1. Januar, ungefähr 50% Rabatt" --language de

# stdin (line-by-line, line structure preserved)
cat transcripts.txt | extended-wer-normalizer -l fr

# File input (shell redirect keeps stdout the single output channel)
extended-wer-normalizer --file transcripts.txt --language fr > normalized.txt

# Introspection
extended-wer-normalizer --describe --language de   # ordered transform list
extended-wer-normalizer --list-languages           # de, en, fr + fallback note

# Pipeline knobs that already exist in the library
extended-wer-normalizer "no no no" --max-repeats 1
```

## Acceptance criteria

- [ ] `[project.scripts]` entry point: `extended-wer-normalizer = "extended_wer_normalizer.cli:main"`.
- [ ] In normalization mode, input is exactly one of: positional `TEXT`,
      `--file PATH`, or stdin (auto-detected when not a TTY). Zero or
      conflicting inputs → usage error on stderr, exit code 2. Introspection
      modes (`--describe`, `--list-languages`) take no input and are exempt
      from this rule.
- [ ] `--language/-l` accepts any code; known codes (`de`, `en`, `fr`) use the
      full pipeline, unknown codes use the minimal fallback and print a
      one-line notice to **stderr** (stdout stays machine-clean).
- [ ] File/stdin input is normalized **line by line**, empty lines preserved,
      trailing newline behavior identical to `cat`.
- [ ] `--describe` prints the ordered list of transforms for the selected
      language (class names, one per line) and exits 0.
- [ ] `--list-languages` prints `supported_languages()` output.
- [ ] `--max-repeats N` is forwarded to `CollapseRepetitions`.
- [ ] Normalized text goes to stdout; all diagnostics go to stderr.
- [ ] Exit codes: `0` success, `1` runtime error (e.g. unreadable file), `2`
      usage error.
- [ ] **No new runtime dependencies** — stdlib `argparse` only.
- [ ] Tests cover: positional input, stdin, `--file`, `--describe`,
      `--list-languages`, unknown-language fallback notice, conflicting-input
      error. Use `pytest` + `capsys` (or `subprocess.run` on the installed
      script for one smoke test).
- [ ] README gains a "Command line" section with the examples above.

## Out of scope (separate tickets)

- YAML/JSON-configurable pipelines or user-supplied preset files.
- A `--compare REF HYP` mode that runs `jiwer.wer` directly.
- Batch/directory processing, globbing, parallel workers.

## Implementation notes

- New module `src/extended_wer_normalizer/cli.py`; keep it thin — all logic
  stays in the existing pipeline builders.
- Reuse `extended_wer_normalizer.normalize_for_wer` /
  `{english,german,french}_wer_pipeline` rather than re-implementing selection
  logic; if pipeline-by-language lookup isn't already centralized, add a small
  `get_pipeline(language, *, max_repeats=...)` helper and let both the public
  API and the CLI call it.
- `--describe` can introspect a `jiwer.Compose` object's `transforms`
  attribute (list of transform instances) — print `type(t).__name__`.
- Follow the exit-code/stderr conventions above so the CLI composes in Unix
  pipelines (`| xargs`, `| diff`, `| wc -l`).
- Version bump: minor (new feature, no breaking change) → `0.7.0`.

## Reference

- Gladia CLI docs: <https://github.com/gladiaio/normalization#cli>
- Gladia implementation: `normalization/cli.py`, `normalization/__main__.py`
  in the same repo (argparse-style, supports `python -m normalization` as
  well — trivial to mirror by adding a `__main__.py` that calls `cli.main()`).
