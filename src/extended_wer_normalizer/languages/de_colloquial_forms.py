"""Spoken German short forms mapped to their full written form.

STTs and human transcribers disagree on whether to write what was said
("hab", "gibt's") or the full form ("habe", "gibt es"). Without this map the
same utterance scores one error per word depending on transcription style.

Inclusion rule. A short form is listed only if it has exactly one full form
and is not itself a different standard word:

- "könnt" is left out: it is also the present tense "ihr könnt", so mapping
  it to "könnte" would hide a real tense error.
- "aufn" is left out: it can mean "auf den" or "auf einen".
- "ne" is left out: it can mean "eine", "nein" ("ne, danke") or "nicht
  wahr" ("oder ne?").

Keys are the forms left after punctuation removal, so "gibt's", "gibt’s"
and "gibts" all arrive as "gibts". No value is itself a key.
"""

DE_COLLOQUIAL_FORMS: dict[str, str] = {
    # Dropped final -e (apocope).
    "glaub": "glaube",
    "gern": "gerne",
    "hab": "habe",
    "hätt": "hätte",
    "möcht": "möchte",
    "nehm": "nehme",
    "wär": "wäre",
    "würd": "würde",
    # Dropped "ei-" of the indefinite article (aphaeresis).
    "nem": "einem",
    "nen": "einen",
    "ner": "einer",
    # Joined short words (clitics).
    "aufm": "auf dem",
    "gehts": "geht es",
    "gibts": "gibt es",
    "ham": "haben",
    "is": "ist",
    # Spelling variants.
    "okay": "ok",
    "tschau": "ciao",
}
