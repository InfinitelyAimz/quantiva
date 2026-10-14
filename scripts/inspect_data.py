"""Convenience wrapper; equivalent to quantiva inspect."""

import sys

from quantiva.cli import main

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "inspect"]
    main()
