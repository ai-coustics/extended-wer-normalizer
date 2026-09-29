# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions before 0.6.0 predate this changelog.

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
