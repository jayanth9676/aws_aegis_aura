"""Command-line entrypoints for the Aegis ML suite."""

from .train import main as train_main
from .batch import main as batch_main

__all__ = ["train_main", "batch_main"]


