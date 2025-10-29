from __future__ import annotations

import argparse
import logging

from configs import AppConfig
from batch import run_batch_inference


LOGGER = logging.getLogger("aegis.cli.batch")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run batch inference for Aegis models")
    parser.add_argument("--data-dir", type=str, default="datasets/ml_sdv_datasets")
    parser.add_argument("--output-dir", type=str, default="model_output")
    parser.add_argument("--limit", type=int, default=None)
    return parser


def parse_args(argv=None) -> AppConfig:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AppConfig(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
    )
    return config, args.limit


def main(argv=None) -> None:
    logging.basicConfig(level=logging.INFO)
    config, limit = parse_args(argv)
    output_path = run_batch_inference(config, limit=limit)
    LOGGER.info("Batch inference completed -> %s", output_path)


if __name__ == "__main__":  # pragma: no cover
    main()


