# extended-wer-normalizer

jiwer-compatible text normalizer for Word Error Rate (WER) evaluation in voice AI.

Extends [jiwer](https://github.com/jitsi/jiwer)'s built-in transforms with normalizations that matter for real-world ASR evaluation: phone numbers, emails, URLs, currency, percentages, ordinals, filler words, and stuttering.

## Installation

```bash
pip install extended-wer-normalizer
```

## Quick start

```python
from extended_wer_normalizer import normalize_for_wer

normalize_for_wer("Call 0176 or email info@example.com, it costs $5.99")
# → "call 0 1 7 6 or email info at example dot com it costs 5 dollars 9 9 cents"

normalize_for_wer("Um, 1st place goes to Dr. Smith with 50% accuracy")
# → "first place goes to doctor smith with 5 0 percent accuracy"
```

## Command line

The package installs an `extended-wer-normalizer` CLI (also runnable as
`python -m extended_wer_normalizer`):

```bash
extended-wer-normalizer 'Call 0176 or email info@example.com'
# → call 0 1 7 6 or email info at example dot com

extended-wer-normalizer 'Hr. Müller, am 1. Januar' --language de
# → herr müller am erste januar

cat transcripts.txt | extended-wer-normalizer -l fr      # stdin, line by line
extended-wer-normalizer --file transcripts.txt -l fr > normalized.txt

extended-wer-normalizer --describe -l de                 # ordered transform list
extended-wer-normalizer --list-languages                 # de, en, fr
```

Exit codes: `0` success, `1` runtime error (e.g. unreadable file), `2` usage
error (missing or conflicting inputs). Diagnostics go to stderr; stdout
carries only normalized text, so the CLI composes with `| diff`, `| wc -l`,
etc.

## jiwer integration

Every normalization is a `jiwer.AbstractTransform` subclass — compose them freely:

```python
import jiwer
from extended_wer_normalizer.transforms import NormalizeEmails, ExpandDigitRuns

pipeline = jiwer.Compose([
    NormalizeEmails(),
    ExpandDigitRuns(),
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.ReduceToListOfListOfWords(),
])

wer = jiwer.wer("info at example dot com", "info@example.com", hypothesis_transform=pipeline)
```

Use the pre-built pipeline with `jiwer.wer`. The pipelines return strings, so append `jiwer.ReduceToListOfListOfWords()` — jiwer requires a transform that ends in word lists:

```python
import jiwer
from extended_wer_normalizer import english_wer_pipeline

transform = jiwer.Compose([english_wer_pipeline, jiwer.ReduceToListOfListOfWords()])
wer = jiwer.wer(reference, hypothesis, reference_transform=transform, hypothesis_transform=transform)
```

## Available transforms

| Transform | Example |
|---|---|
| `CompoundSpokenNumbersToDigits` | `"twenty one"` → `"21"`, `"einundzwanzig"` → `"21"` (with `language="de"`) |
| `ExpandDigitRuns` | `"0176"` → `"0 1 7 6"` |
| `DigitWordsToChars` | `"zero one seven"` → `"0 1 7"` |
| `NormalizeEmails` | `"user@example.com"` → `"user at example dot com"` |
| `NormalizeURLs` | `"https://example.com/path"` → `"example dot com"` |
| `NormalizeCurrency` | `"$5.99"` → `"five dollars ninety nine cents"` |
| `NormalizePercentages` | `"50%"` → `"fifty percent"` |
| `NormalizeOrdinals` | `"1st"` → `"first"`, `"15th"` → `"fifteenth"` |
| `ExpandAbbreviations` | `"Dr."` → `"doctor"`, `"vs."` → `"versus"` |
| `NormalizeSymbols` | `"cats & dogs"` → `"cats and dogs"` |
| `SplitHyphenatedWords` | `"fixed-term"` → `"fixed term"` |
| `RemoveFillerWords` | removes `um`, `uh`, `hmm`, `er`, `ah`, … |
| `CollapseRepetitions` | `"yes yes yes yes"` → `"yes"` (collapses runs of 4+; configurable via `max_repeats`) |
| `ExpandFrenchElisions` | `"j'aime"` → `"j aime"`, `"qu'il"` → `"qu il"` (French only) |

Every transform that consumes language-specific data accepts a `language="en"` keyword (default English): `NormalizeEmails(language="fr")`, `ExpandAbbreviations(language="de")`, etc.

## Pipeline design

The English pipeline applies transforms left-to-right in a single pass:

1. **Pattern-specific** (before punctuation is stripped): email, URL, symbol, abbreviation, currency, percentage, ordinal
2. **Core**: contractions (`I'm` → `i am`), compound number words to digits (`twenty one` → `21`), lowercase, intra-word hyphen split (`fixed-term` → `fixed term`), punctuation removal
3. **Digit normalization**: expand digit runs (`0176` → `0 1 7 6`, `21` → `2 1`), convert digit words (`zero` → `0`)
4. **Cleanup**: filler words, repetition collapse

## Supported languages

Full pipelines (with language-specific abbreviations, fillers, lexicons, and number/ordinal/percentage word forms via `num2words`) ship for **English**, **German**, and **French**. Pass any other `language` value for the minimal fallback (lowercase, intra-word hyphen split, punctuation and whitespace cleanup, repetition collapse).

```python
from extended_wer_normalizer import normalize_for_wer

# German: titles, fillers, ordinals, currency
normalize_for_wer("Hr. Müller, am 1. Januar, ähm, ungefähr 50% Rabatt", language="de")
# → "herr müller am erste januar ungefähr 5 0 prozent rabatt"

# French: elision contractions, ordinals, comma-decimal currency
normalize_for_wer("M. Dupont, le 1er janvier, c'est €5,99", language="fr")
# → "monsieur dupont le premier janvier c est 5 euros 9 9 centimes"

# Spanish, Italian, … fall through to the minimal pipeline
normalize_for_wer("¡Hola, mundo!", language="es")
# → "hola mundo"

# Tune the repetition-collapse threshold (default 3 → collapse runs of 4+)
normalize_for_wer("no no no", max_repeats=1)  # collapse any 2+ run
# → "no"
```

Per-language pipelines are also exposed for direct use with `jiwer.wer`:

```python
from extended_wer_normalizer import (
    english_wer_pipeline,
    german_wer_pipeline,
    french_wer_pipeline,
)
```

To inspect or extend the language data:

```python
from extended_wer_normalizer.languages import get_language_data, supported_languages

supported_languages()              # ["de", "en", "fr"]
get_language_data("de").abbreviations["hr."]  # "herr"
```

### Quirks worth knowing

- **Currency and percentages canonicalize to digits, not words.** `NormalizeCurrency`/`NormalizePercentages` first verbalize amounts (`$5.99` → `five dollars ninety nine cents`, `50%` → `fifty percent` — the per-transform outputs shown in the table above), but the digit-normalization stage (`CompoundSpokenNumbersToDigits`, then `ExpandDigitRuns`) runs later in the pipeline and converts those number words back to split digits: the pipeline's final form is `5 dollars 9 9 cents` / `5 0 percent`. Written and spoken forms still converge to the same string, which is what WER fairness needs — except for amounts with a trailing currency symbol (`5,99 €`), which are not yet recognized (ML-1801).
- **Hyphenated compounds**: intra-word hyphens split into spaces (`fixed-term` → `fixed term`), so hyphenated and spaced spellings of the same words score identically. Before 0.6.0 the hyphen was deleted (`fixedterm`), which penalized STTs that never emit hyphens — WER numbers are not comparable across that boundary.
- **Comma vs. period decimals**: French uses `,` (`€5,99`, `3,5%`); the currency and percentage transforms accept either separator regardless of language.
- **German ordinals**: matched as 1- to 3-digit numbers followed by `. ` and a word (e.g. `"1. Januar"` but not `"Es war 1990."` or `"1.5 Liter"`). 4+ digits and decimals are skipped to avoid false positives on years.
- **French ordinals**: matched as `1er`, `1ère`, `2e`, `2es`, `2ème`, `2èmes`, `2nde`, `2nds`, `2nd`. `num2words` returns masculine forms (`premier`, `deuxième`); feminine variants like `première` or `seconde` are not produced.
- **Contractions**: `jiwer.ExpandCommonEnglishContractions` runs only for English. French has a custom `ExpandFrenchElisions` that splits `j'`, `l'`, `d'`, `n'`, `s'`, `m'`, `t'`, `c'`, `qu'`, `jusqu'`, `lorsqu'`, `puisqu'`, `quoiqu'` from the following word. German has no contraction step.
- **German pluralization**: most currency units stay invariant (`fünf Euro`, not `fünf Euros`).
