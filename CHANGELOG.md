# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions before 0.6.0 predate this changelog.

## [Unreleased]

### Added

- **English US/UK spelling-variant canonicalization** (British → American):
  `travelling` → `traveling`, `colour` → `color`, `centre` → `center`.
  Previously, a hypothesis and reference differing only in dialect spelling
  scored one substitution per differing word. The 1,737-entry table is
  based on OpenAI Whisper's `whisper/normalizers/english.json` (MIT) —
  the same source gladiaio/normalization draws on — with a small number of
  documented corrections to upstream entries that change morphology rather
  than spelling (`pummelled` → `pummeled`, `pummelling` → `pummeling`,
  `snowploughs` → `snowplows`, and the `tranquilly` → `tranquility`
  mapping removed) plus two scraping-artifact cleanups; see
  `languages/en_spelling_variants.py` for the full deviation list.
  Normalized output diverges from Whisper/Gladia on exactly those tokens.
- New transform `NormalizeSpellingVariants`, applied in the full pipelines
  after punctuation removal. No-op for languages without a table (currently
  de, fr) and not part of the minimal fallback pipeline.
- **WER numbers computed with ≤ 0.6.0 are not comparable to ≥ 0.7.0 for
  English text containing dialect spelling variation** — such pairs now
  score zero instead of one substitution per word. Recompute cached results
  before comparing across the boundary.

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
