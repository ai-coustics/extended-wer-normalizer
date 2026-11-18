# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions before 0.6.0 predate this changelog.

## [Unreleased]

**WER numbers are not comparable across this release** for English text
with typographic apostrophes, the spellings listed below, given names with
variant spellings, or `okay`; for German text with spoken short forms or
joined spellings (`nochmal`); and for English, German and French text with
digits inside a word (`user123`).

### Added

- `NormalizeApostrophes` transform, run in the English pipeline before
  contraction expansion.
- `NormalizeNameVariants` transform and `LanguageData.name_variants` field
  (ML-2059). English merges spellings of the same given name that sound
  identical (`Stephen` → `Steven`, `Balthasar` → `Balthazar`), since no STT
  can tell them apart from audio. The curated table and its inclusion rule
  live in `languages/en_name_variants.py`. Runs after spelling variants.
- 148 British → American spelling entries beyond the Whisper-derived table
  (ML-2059): the -isation nouns and plurals of -ise verbs already in the
  table (`authorisation` → `authorization`, `civilisation` →
  `civilization`) and -centre compounds (`telecentre` → `telecenter`).
- `NormalizeColloquialForms` transform and `LanguageData.colloquial_forms`
  field (ML-2122). German maps spoken short forms to the full form, so
  transcripts that write what was said and transcripts that write the full
  form score the same: `hab` → `habe`, `nen` → `einen`, `gibt's` → `gibt es`,
  `aufm` → `auf dem`, `tschau` → `ciao`. Ambiguous forms are left alone:
  `ne` (eine, nein or "right?"), `könnt` (also present tense) and `aufn`
  (auf den or auf einen). The table and its inclusion rule live in
  `languages/de_colloquial_forms.py`. English and German map `okay` → `ok`,
  matching `OK` and `O.K.`
- German spelling variants (ML-2122): words written joined or split map to
  the split form, `nochmal` → `noch mal`, `sodass` → `so dass`, `wieviel(e)`
  → `wie viel(e)`, `garnicht` → `gar nicht`, `zuhause` → `zu hause`. The
  last one also merges the noun `das Zuhause` with the adverb. `zurzeit` is
  left out because it means something different from `zur Zeit`.

### Fixed

- English contractions with a typographic apostrophe now expand like the
  ASCII form (ML-2059): `He’s married` normalized to `hes married` and
  `don’t` to `dont`; both now give `he is married` and `do not`. Quote marks
  at word edges (`‘sorry’`) are unchanged.
- Digits inside a word are split off before digit runs are expanded
  (ML-2122, English, German and French, new `SplitLetterDigitBoundaries`
  transform): `user123` normalized to `user1 2 3` and now gives
  `user 1 2 3`, matching `user one two three`. Numbers with a unit or
  suffix (`5mm`, `4th`) are unchanged.

## [0.8.0] - 2026-10-27

**WER numbers are not comparable across this release**: decimals, grouped
thousands and large English amounts all normalize differently.

### Added

- `RemoveThousandsSeparators`, `NormalizeDecimals` and
  `DropCurrencyConjunction` transforms, plus the `thousands_separators` /
  `decimal_word` fields on `LanguageData` (en `,` / `point`; de `.` /
  `komma`; fr space, no-break space, `.` / `virgule`).

### Changed

- **Decimals keep their separator** (GitHub #11, ML-1887). `3.5` used to
  normalize to `3 5`, identical to `35`, so an STT writing `35` for "three
  point five" went unpenalized. Written and spoken decimals now converge on
  `3 point 5` (`3 komma 5`, `3 virgule 5`), including percentages (`3.5%` →
  `3 point 5 percent`). Separator chains (IPs, versions, dates) are
  unchanged. UK-style times such as `3.30` now read as decimals and no longer
  match "three thirty".

### Fixed

- Currency and percentages with thousands separators are read as one amount
  (ML-1885): `$12,500` normalized to `1 2 dollars 5 0 cents0` and
  `€1.000` (de) to `1 euro0`; both now match their spoken forms. A currency
  amount with three or more fractional digits (`$5.999`) is read as a decimal
  (`5 point 9 9 9 dollars`) instead of leaving a stray digit behind; every
  written digit is kept, trailing zeros included (`$5.990`, `3.50%`).
- English currency amounts, percentages and ordinals of 1,000 or more that
  aren't round no longer split into two numbers: `$12500` normalized to
  `1 2 0 0 0 5 0 0 dollars` instead of `1 2 5 0 0 dollars`, because
  `num2words` writes "twelve thousand, five hundred" and the comma broke
  re-digitization. Output changes for these inputs (ML-1886).
- Currency amounts with the symbol after the amount, the German and French
  convention, are now recognized (ML-1801): `20 €` normalized to `2 0 €`
  instead of matching "zwanzig euro" (`2 0 euro`). A bare symbol with no
  amount becomes the unit name (`in €` → `in euro`) instead of surviving
  as a stray `€`. New `LanguageData.currency_symbol_trailing` field.
- Spoken amounts joining the major and minor amounts with "and" ("five
  dollars and ninety nine cents"; German "und", French "et") now match the
  written form (`$5.99`) via the new `DropCurrencyConjunction` transform and
  `LanguageData.currency_conjunction` field.
- Amounts under one unit drop the zero major amount: `$0.50` →
  "fifty cents" instead of "zero dollars fifty cents". `$0` still reads
  "zero dollars".
- `£` minor amounts verbalize as "pence" rather than "pennies" (`£10.50` →
  "ten pounds fifty pence"), matching how British amounts are spoken.

## [0.7.0] - 2026-10-27

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
- **English US/UK spelling-variant canonicalization** (British → American):
  `travelling` → `traveling`, `colour` → `color`, `centre` → `center`.
  Previously, a hypothesis and reference differing only in dialect spelling
  scored one substitution per differing word. The 1,731-entry table is
  based on OpenAI Whisper's `whisper/normalizers/english.json` (MIT) —
  the same source gladiaio/normalization draws on — with documented
  corrections to upstream entries that change the word rather than only
  its spelling (`pummelled` → `pummeled`, `pummelling` → `pummeling`,
  `snowploughs` → `snowplows`, `philtre` → `philter`; the `tranquilly`,
  `tonne(s)` and `gage*` mappings removed), five upstream entries that map
  American → British flipped (e.g. `glamour` → `glamor`), and two
  scraping-artifact cleanups; see `languages/en_spelling_variants.py` for
  the full deviation list.
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
