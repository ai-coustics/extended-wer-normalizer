"""Allow `python -m extended_wer_normalizer` as an alias for the CLI."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
