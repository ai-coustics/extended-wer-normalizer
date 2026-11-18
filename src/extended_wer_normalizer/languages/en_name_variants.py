"""Spelling variants of English given names, for WER normalization.

An STT cannot hear whether a speaker said "Steven" or "Stephen": the audio is
identical and context rarely decides the spelling. Scoring that as a
substitution penalizes something no recognizer can get right, the same reason
`en_spelling_variants` merges British and American spellings.

Inclusion rule. A spelling joins a group only if all of these hold:

- It is the same name, not a related one ("Jon"/"John" yes;
  "Johnny"/"John" no).
- It is pronounced the same in English ("Debra"/"Deborah" differ in
  syllables, so they stay apart).
- It is not also a common English word, so ordinary text is never rewritten
  ("Grey"/"Gray" are colours; "Mark" is fine as a canonical value but would
  not be a key).

The canonical value is the most common English spelling of the name. No
canonical value is itself a key, so the map is idempotent.

Curated, not vendored: there is no upstream table. Add groups that meet the
rule, not one-off spellings found in a single dataset.
"""

_GROUPS: dict[str, tuple[str, ...]] = {
    "aidan": ("aiden",),
    # "allen" is left out: "allen key" / "allen wrench" are common nouns.
    "alan": ("allan",),
    "anne": ("ann",),
    "ashley": ("ashleigh",),
    "balthazar": ("balthasar",),
    "brian": ("bryan",),
    "caitlin": ("kaitlyn", "katelyn", "kaitlin"),
    "carl": ("karl",),
    "catherine": ("katherine", "kathryn", "katharine", "catharine"),
    "claire": ("clare",),
    "elliott": ("elliot",),
    "eric": ("erik",),
    "hannah": ("hanna",),
    "isabel": ("isabelle", "isobel"),
    "jacob": ("jakob",),
    "jeffrey": ("geoffrey", "jeffery"),
    "john": ("jon",),
    "lindsay": ("lindsey",),
    "mark": ("marc",),
    "matthew": ("mathew",),
    "muhammad": ("mohammed", "mohammad", "mohamed", "muhammed"),
    "nicholas": ("nicolas",),
    "philip": ("phillip",),
    "rachel": ("rachael",),
    "sarah": ("sara",),
    "sean": ("shawn", "shaun"),
    # "sofia" is left out: it is also the capital of Bulgaria.
    "steven": ("stephen",),
    "teresa": ("theresa",),
    "zachary": ("zachery", "zackary"),
}

EN_NAME_VARIANTS: dict[str, str] = {
    variant: canonical for canonical, variants in _GROUPS.items() for variant in variants
}
