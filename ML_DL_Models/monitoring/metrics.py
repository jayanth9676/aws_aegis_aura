from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def log_metrics(metrics: Dict[str, Dict[str, float]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "metrics_summary.json"
    path.write_text(json.dumps(metrics, indent=2))
    return path


