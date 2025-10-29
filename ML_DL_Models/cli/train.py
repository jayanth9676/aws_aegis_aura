from __future__ import annotations

import argparse
import logging
from pathlib import Path

from configs import AppConfig
from data import load_datasets
from training import train_all_models, train_autoencoder_only


LOGGER = logging.getLogger("aegis.cli.train")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train Aegis APP fraud detection models")
    parser.add_argument("--data-dir", type=str, default="datasets/ml_sdv_datasets")
    parser.add_argument("--output-dir", type=str, default="model_output")
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--shap-sample", type=int, default=200)
    parser.add_argument("--autoencoder-only", action="store_true",
                       help="Train only the autoencoder model (requires fraud models to be trained first)")
    parser.add_argument("--generate-mule-data", action="store_true",
                       help="Generate synthetic mule account data before training")
    parser.add_argument("--include-mule-data", action="store_true", default=True,
                       help="Include mule data in training (default: True)")
    parser.add_argument("--no-mule-data", action="store_true",
                       help="Exclude mule data from training")
    parser.add_argument("--include-gnn", action="store_true",
                       help="Train GNN models for graph-based fraud detection")
    parser.add_argument("--include-transformers", action="store_true",
                       help="Train Transformer models for sequence and categorical feature analysis")
    parser.add_argument("--include-rl", action="store_true",
                       help="Train Reinforcement Learning policy for dynamic decision optimization")
    return parser


def parse_args(argv=None) -> tuple[AppConfig, bool, bool, bool, bool, bool, bool, bool]:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AppConfig(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        max_rows=args.max_rows,
        test_size=args.test_size,
        random_state=args.random_state,
        shap_sample=args.shap_sample,
    )
    
    # Handle mule data options
    include_mule_data = args.include_mule_data and not args.no_mule_data
    
    return config, args.autoencoder_only, args.generate_mule_data, include_mule_data, args.no_mule_data, args.include_gnn, args.include_transformers, args.include_rl


def main(argv=None) -> None:
    # Set up logging with file handler
    log_dir = Path('model_output/logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / 'training.log', mode='w')
        ]
    )

    config, autoencoder_only, generate_mule_data, include_mule_data, no_mule_data, include_gnn, include_transformers, include_rl = parse_args(argv)

    # Generate mule data if requested
    if generate_mule_data:
        LOGGER.info("Generating synthetic mule data")
        try:
            from datasets.mule_account_generator import generate_all_mule_data
            generate_all_mule_data()
            LOGGER.info("Mule data generation completed")
        except Exception as e:
            LOGGER.error(f"Mule data generation failed: {e}", exc_info=True)
            raise

    if autoencoder_only:
        LOGGER.info("Starting Aegis autoencoder-only training")
        try:
            artifacts = train_autoencoder_only(config)
            LOGGER.info(f"Autoencoder training completed successfully. Artifacts: {list(artifacts.keys())}")
        except Exception as e:
            LOGGER.error(f"Autoencoder training failed: {e}", exc_info=True)
            raise
    else:
        LOGGER.info("Starting Aegis ML training pipeline")
        if no_mule_data:
            LOGGER.info("Excluding mule data from training")
        elif include_mule_data:
            LOGGER.info("Including mule data in training")
        
        try:
            datasets = load_datasets(config, include_mule_data=include_mule_data)
            artifacts = train_all_models(
                config, 
                datasets, 
                include_mule_data=include_mule_data,
                include_gnn=include_gnn,
                include_transformers=include_transformers,
                include_rl=include_rl,
            )
            
            if include_gnn:
                LOGGER.info("GNN training enabled - models will be trained if dependencies are available")
            if include_transformers:
                LOGGER.info("Transformer training enabled - models will be trained if dependencies are available")
            if include_rl:
                LOGGER.info("Reinforcement Learning training enabled - models will be trained if dependencies are available")
            
            LOGGER.info(f"Training completed successfully. Artifacts: {list(artifacts.keys())}")
        except Exception as e:
            LOGGER.error(f"Training failed: {e}", exc_info=True)
            raise


if __name__ == "__main__":  # pragma: no cover
    main()


