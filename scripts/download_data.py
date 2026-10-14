"""Convenience wrapper; equivalent to quantiva download."""

from quantiva.config import Settings
from quantiva.ingestion import download_dataset

if __name__ == "__main__":
    download_dataset(Settings.from_environment().raw_file)
