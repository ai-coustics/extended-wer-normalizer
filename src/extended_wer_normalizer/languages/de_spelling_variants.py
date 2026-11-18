"""German words that are written joined or split, mapped to the split form.

Both spellings are in use ("nochmal" / "noch mal") and sound the same, so
transcripts differ only in style. The map goes joined → split because the
token lookup replaces one word at a time and cannot join two.

Listed only when the two forms mean the same. "zurzeit" ("currently") vs.
"zur Zeit" ("at the time of") is left out. "zuhause" also merges the noun
"das Zuhause" with the adverb "zu Hause"; accepted, since the words sound
the same.
"""

DE_SPELLING_VARIANTS: dict[str, str] = {
    "garnicht": "gar nicht",
    "nochmal": "noch mal",
    "sodass": "so dass",
    "wieviel": "wie viel",
    "wieviele": "wie viele",
    "zuhause": "zu hause",
}
