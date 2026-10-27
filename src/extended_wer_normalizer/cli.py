"""Command-line interface: normalize text for WER evaluation from the shell.

Installed as the `extended-wer-normalizer` console script and mirrored by
`python -m extended_wer_normalizer`. Normalized text goes to stdout, all
diagnostics to stderr; exit codes are 0 (success), 1 (runtime error), and
2 (usage error, via argparse).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

import jiwer

from . import DEFAULT_MAX_REPEATS, get_pipeline, supported_languages

PROG = "extended-wer-normalizer"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=(
            "Normalize text for WER evaluation. Full pipelines exist for "
            f"{', '.join(supported_languages())}; any other --language code uses the "
            "minimal fallback (lowercase, hyphen splitting, punctuation and "
            "whitespace cleanup, repetition collapse)."
        ),
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="text to normalize (takes precedence over piped stdin; "
        "omit both this and --file to read stdin)",
    )
    parser.add_argument("--file", metavar="PATH", help="read input from PATH (UTF-8), line by line")
    parser.add_argument(
        "-l",
        "--language",
        default="en",
        help="language code (default: %(default)s)",
    )
    parser.add_argument(
        "--max-repeats",
        type=int,
        default=DEFAULT_MAX_REPEATS,
        metavar="N",
        help="collapse word repetitions longer than N (default: %(default)s, "
        "i.e. runs of N+1 or more)",
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help="print the ordered transform list for --language and exit",
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="print the language codes with full pipelines and exit",
    )
    return parser


def _normalize(pipeline: jiwer.Compose, text: str) -> str:
    # Same as normalize_for_wer, with the pipeline resolved once by the caller.
    return pipeline([text])[0].strip()


def _normalize_lines(lines: Iterable[str], pipeline: jiwer.Compose) -> None:
    """Normalize input one line at a time, preserving line structure.

    A trailing newline is emitted only for lines that had one, matching cat.
    """
    for line in lines:
        has_newline = line.endswith("\n")
        normalized = _normalize(pipeline, line.rstrip("\n"))
        sys.stdout.write(normalized + ("\n" if has_newline else ""))


def _use_utf8_stdio() -> None:
    """Read stdin and write stdout as UTF-8, matching `--file`.

    The platform default differs on Windows (cp1252 for pipes), which would
    make piped and `--file` input normalize differently.
    """
    for stream in (sys.stdin, sys.stdout):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.max_repeats < 1:
        parser.error("--max-repeats must be >= 1")

    _use_utf8_stdio()

    if args.list_languages:
        for code in supported_languages():
            print(code)
        print("any other code falls back to the minimal pipeline")
        return 0

    if args.language not in supported_languages():
        print(
            f"{PROG}: no full pipeline for language {args.language!r}; using the minimal fallback",
            file=sys.stderr,
        )
    pipeline = get_pipeline(args.language, args.max_repeats)

    if args.describe:
        for transform in pipeline.transforms:
            print(type(transform).__name__)
        return 0

    # Explicit inputs win over stdin, which is only consulted when neither is
    # given — otherwise `cli "text" < /dev/null` (stdin open but irrelevant)
    # would be a spurious conflict. TEXT + --file is the only true conflict.
    if args.text is not None and args.file is not None:
        parser.error("provide only one of TEXT or --file PATH")
    if args.text is None and args.file is None and sys.stdin.isatty():
        parser.error("no input: provide TEXT, --file PATH, or piped stdin")

    try:
        if args.text is not None:
            print(_normalize(pipeline, args.text))
        elif args.file is not None:
            with open(args.file, encoding="utf-8") as lines:
                _normalize_lines(lines, pipeline)
        else:
            _normalize_lines(sys.stdin, pipeline)
    except (OSError, UnicodeError) as exc:
        print(f"{PROG}: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
