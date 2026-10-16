# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions before 0.6.0 predate this changelog.

## [0.7.0] - 2026-10-16

### Added

- Command-line interface, installed as `extended-wer-normalizer` and mirrored
  by `python -m extended_wer_normalizer`. Normalizes positional text, a
  `--file`, or piped stdin (line by line, line structure preserved);
  `--language/-l` selects the pipeline (unknown codes fall back to the minimal
  pipeline with a stderr notice), `--max-repeats` tunes repetition collapsing,
  `--describe` prints the ordered transform list, `--list-languages` prints
  the full-pipeline language codes. Normalized text goes to stdout and
  diagnostics to stderr; exit codes are 0 (success), 1 (runtime error),
  2 (usage error).
- Public `get_pipeline(language, max_repeats=...)` helper: the
  pipeline-selection logic previously private inside `normalize_for_wer`, now
  shared between the API and the CLI.

## [0.6.0] - 2026-09-28

### Changed

- **Hyphenated compounds are now split, not joined** (ML-1725). Intra-word
  hyphens normalize to a space (`fixed-term` → `fixed term`) instead of being
  deleted (`fixed-term` → `fixedterm`). Previously, a hypothesis writing
  `fixed term` against a reference of `fixed-term` scored 1 substitution + 1
  insertion although the words are identical — a systematic bias against STT
  engines that never emit hyphens (e.g. Deepgram Nova-3), which showed up as a
  measurable WER penalty for those engines on hyphen-rich references.
- New language-agnostic transform `SplitHyphenatedWords`, applied in the full
  pipelines (after `CompoundSpokenNumbersToDigits`, before punctuation
  removal) and in the minimal fallback pipeline.
- **WER numbers computed with ≤ 0.5.x are not comparable to ≥ 0.6.0.** The
  split also enlarges reference word counts for hyphenated GT (compound errors
  now count per part), so recompute cached results — including any
  `ref_len`-derived columns — before comparing across the boundary.
