"""Aegis ML toolkit for APP fraud detection.

This package centralizes configuration, data loading, feature engineering,
model training, and inference utilities required to operationalize the
advanced hybrid models described in the Aegis PRDs.

All utilities are designed to be SageMaker-friendly (stateless functions,
explicit configuration, and serializable artifacts) and memory-aware to allow
training inside managed notebook instances or training jobs.
"""

from importlib import metadata


def __getattr__(name: str):  # pragma: no cover - lightweight version helper
    if name == "__version__":
        try:
            return metadata.version("agenticai-for-authorized-push-payments")
        except metadata.PackageNotFoundError:
            return "0.0.0"
    raise AttributeError(name)


__all__ = ["__version__"]


