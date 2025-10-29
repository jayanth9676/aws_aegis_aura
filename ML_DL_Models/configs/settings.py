from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


def _env_path(key: str, default: str) -> Path:
    value = os.environ.get(key, default)
    return Path(value).expanduser().resolve()


@dataclass(slots=True)
class AppConfig:
    """Application-level settings for training and inference.

    The configuration is purpose-built for SageMaker environments where paths are
    typically mounted under ``/opt/ml`` and environment variables drive runtime
    selection. We retain compatibility with local development by providing sensible
    defaults and allowing overrides through CLI arguments.
    """

    data_dir: Path = field(default_factory=lambda: _env_path("AEGIS_DATA_DIR", "datasets/ml_sdv_datasets"))
    metadata_file: str = os.environ.get("AEGIS_METADATA_FILE", "aegis_metadata.json")
    output_dir: Path = field(default_factory=lambda: _env_path("AEGIS_OUTPUT_DIR", "model_output"))
    model_artifacts_s3: Optional[str] = os.environ.get("AEGIS_MODEL_ARTIFACTS_S3")
    max_rows: Optional[int] = None
    enable_gpu: bool = os.environ.get("AEGIS_ENABLE_GPU", "0") == "1"
    random_state: int = int(os.environ.get("AEGIS_RANDOM_STATE", "42"))
    test_size: float = float(os.environ.get("AEGIS_TEST_SIZE", "0.2"))
    shap_sample: int = int(os.environ.get("AEGIS_SHAP_SAMPLE", "200"))
    shap_background: int = int(os.environ.get("AEGIS_SHAP_BACKGROUND", "500"))
    behavioral_max_seq_len: int = int(os.environ.get("AEGIS_BEHAVIORAL_MAX_SEQ_LEN", "32"))
    autoencoder_hidden_dim: int = int(os.environ.get("AEGIS_AUTOENCODER_HIDDEN", "128"))
    chunk_size: int = int(os.environ.get("AEGIS_CHUNK_SIZE", "10000"))
    max_memory_gb: float = float(os.environ.get("AEGIS_MAX_MEMORY_GB", "8.0"))

    def __post_init__(self) -> None:
        if not isinstance(self.data_dir, Path):
            self.data_dir = Path(self.data_dir).expanduser().resolve()
        else:
            self.data_dir = self.data_dir.expanduser().resolve()
        if not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir).expanduser().resolve()
        else:
            self.output_dir = self.output_dir.expanduser().resolve()

    def ensure_paths(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "logs").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "artifacts").mkdir(parents=True, exist_ok=True)

    @property
    def metadata_path(self) -> Path:
        return self.data_dir / self.metadata_file

    def export(self) -> Dict[str, Any]:
        return {
            "data_dir": str(self.data_dir),
            "metadata_path": str(self.metadata_path),
            "output_dir": str(self.output_dir),
            "model_artifacts_s3": self.model_artifacts_s3,
            "max_rows": self.max_rows,
            "enable_gpu": self.enable_gpu,
            "random_state": self.random_state,
            "test_size": self.test_size,
            "shap_sample": self.shap_sample,
            "shap_background": self.shap_background,
            "behavioral_max_seq_len": self.behavioral_max_seq_len,
            "autoencoder_hidden_dim": self.autoencoder_hidden_dim,
            "chunk_size": self.chunk_size,
            "max_memory_gb": self.max_memory_gb,
        }

    def dump_json(self, path: Optional[Path] = None) -> Path:
        path = path or (self.output_dir / "config_snapshot.json")
        path.write_text(json.dumps(self.export(), indent=2))
        return path


