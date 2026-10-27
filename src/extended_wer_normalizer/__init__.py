"""extended-wer-normalizer: jiwer-compatible WER normalization for voice AI."""

from __future__ import annotations

import jiwer

from .languages import supported_languages
from .transforms import (
    CollapseRepetitions,
    CompoundSpokenNumbersToDigits,
    DigitWordsToChars,
    DropCurrencyConjunction,
    ExpandAbbreviations,
    ExpandDigitRuns,
    ExpandFrenchElisions,
    NormalizeCurrency,
    NormalizeDecimals,
    NormalizeEmails,
    NormalizeOrdinals,
    NormalizePercentages,
    NormalizeSpellingVariants,
    NormalizeSymbols,
    NormalizeURLs,
    RemoveFillerWords,
    RemoveThousandsSeparators,
    SplitHyphenatedWords,
)

__all__ = [
    "get_pipeline",
    "normalize_for_wer",
    "supported_languages",
    "english_wer_pipeline",
    "german_wer_pipeline",
    "french_wer_pipeline",
    "CollapseRepetitions",
    "CompoundSpokenNumbersToDigits",
    "DigitWordsToChars",
    "DropCurrencyConjunction",
    "ExpandAbbreviations",
    "ExpandDigitRuns",
    "ExpandFrenchElisions",
    "NormalizeCurrency",
    "NormalizeDecimals",
    "NormalizeEmails",
    "NormalizeOrdinals",
    "NormalizePercentages",
    "NormalizeSpellingVariants",
    "NormalizeSymbols",
    "NormalizeURLs",
    "RemoveFillerWords",
    "RemoveThousandsSeparators",
    "SplitHyphenatedWords",
]


DEFAULT_MAX_REPEATS = 3


def _build_pipeline(language: str, max_repeats: int = DEFAULT_MAX_REPEATS) -> jiwer.Compose:
    """Compose a WER-normalization pipeline for `language`.

    Supported languages ("en", "de", "fr") get the full structure. Any other
    language falls back to a minimal language-agnostic pipeline: lowercase,
    intra-word hyphen splitting, punctuation/whitespace cleanup, and
    repetition collapse.
    """
    if language not in supported_languages():
        return jiwer.Compose(
            [
                jiwer.ToLowerCase(),
                SplitHyphenatedWords(),
                jiwer.RemovePunctuation(),
                jiwer.RemoveMultipleSpaces(),
                jiwer.Strip(),
                CollapseRepetitions(max_repeats),
            ]
        )

    steps: list = [
        # Pattern-specific normalizations run first, before punctuation is stripped.
        NormalizeEmails(language),
        NormalizeURLs(language),
        # After emails/URLs (which verbalize their own dots), before currency
        # and percent, which would read "12,500" as 12 point 5.
        RemoveThousandsSeparators(language),
        NormalizeSymbols(language),
        ExpandAbbreviations(language),
        NormalizeCurrency(language),
        NormalizePercentages(language),
        NormalizeOrdinals(language),
    ]

    # Language-specific contraction handling.
    if language == "en":
        steps.append(jiwer.ExpandCommonEnglishContractions())
    elif language == "fr":
        steps.append(ExpandFrenchElisions())
    # German has no separate contraction expansion step.

    steps.extend(
        [
            # Compound-number → digit runs BEFORE punctuation removal so that
            # French hyphenated forms ("quatre-vingt-quatorze") and German
            # closed compounds ("einundzwanzig") still carry their structure
            # when text2num looks at them. text2num is case-insensitive, so
            # placement before ToLowerCase is fine. The resulting digit block
            # (e.g. "twenty one" → "21") is then split into "2 1" by
            # ExpandDigitRuns, matching the canonical form for "21".
            CompoundSpokenNumbersToDigits(language),
            # "3.5" (written, or from spoken "three point five") → "3 point 5"
            # before RemovePunctuation can collapse it into "35".
            NormalizeDecimals(language),
            # "5 dollars and 99 cents" → "5 dollars 99 cents", as "$5.99" reads.
            DropCurrencyConjunction(language),
            jiwer.ToLowerCase(),
            # Split "fixed-term" → "fixed term" before RemovePunctuation, which
            # would otherwise delete the hyphen and join the parts. After
            # CompoundSpokenNumbersToDigits so hyphenated number words
            # ("twenty-one", "quatre-vingt-quatorze") keep their structure.
            SplitHyphenatedWords(),
            jiwer.RemovePunctuation(),
            # Spelling variants map whole tokens, so they need punctuation
            # already removed ("colour," → "colour") and lowercase applied.
            NormalizeSpellingVariants(language),
            ExpandDigitRuns(),
            DigitWordsToChars(language),
            jiwer.RemoveMultipleSpaces(),
            jiwer.Strip(),
            # Speech artifact cleanup.
            RemoveFillerWords(language),
            CollapseRepetitions(max_repeats),
        ]
    )
    return jiwer.Compose(steps)


english_wer_pipeline = _build_pipeline("en")
german_wer_pipeline = _build_pipeline("de")
french_wer_pipeline = _build_pipeline("fr")

_PIPELINES: dict[str, jiwer.Compose] = {
    "en": english_wer_pipeline,
    "de": german_wer_pipeline,
    "fr": french_wer_pipeline,
}


def get_pipeline(language: str, max_repeats: int = DEFAULT_MAX_REPEATS) -> jiwer.Compose:
    """Return the WER-normalization pipeline for `language`.

    The prebuilt shared pipelines are returned for the default `max_repeats`;
    a custom threshold or an unsupported language builds a one-off pipeline.
    Unsupported languages get the minimal language-agnostic fallback described
    in `normalize_for_wer`.
    """
    if max_repeats == DEFAULT_MAX_REPEATS and language in _PIPELINES:
        return _PIPELINES[language]
    return _build_pipeline(language, max_repeats)


def normalize_for_wer(
    text: str, language: str = "en", max_repeats: int = DEFAULT_MAX_REPEATS
) -> str:
    """Normalize text for WER comparison.

    Supported full-pipeline languages: "en", "de", "fr". Each runs the same
    structure (pattern normalization → lowercase → intra-word hyphen splitting →
    punctuation removal → spelling-variant canonicalization → digit
    normalization → cleanup) with language-specific lexicons and a custom
    contraction step (English contractions for "en", elision splitting for
    "fr", none for "de"). Spelling-variant canonicalization currently only
    ships a table for English (British → American); it is a no-op elsewhere.

    For any other `language` value, applies a minimal language-agnostic pipeline:
    lowercase, intra-word hyphen splitting, punctuation removal, whitespace
    normalization, and repetition collapse. Useful as a fallback for languages
    that don't yet have a tuned data module.

    `max_repeats` controls the repetition-collapse threshold: a word must repeat
    more than this many times in a row before the run is collapsed to a single
    occurrence (default 3, i.e. runs of 4+ collapse). See `CollapseRepetitions`.
    """
    return get_pipeline(language, max_repeats)([text])[0].strip()
