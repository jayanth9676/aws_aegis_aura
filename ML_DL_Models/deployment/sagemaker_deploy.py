from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import boto3


@dataclass
class SageMakerDeploymentConfig:
    model_package_name: str
    execution_role_arn: str
    endpoint_name: str
    instance_type: str = "ml.m5.xlarge"
    initial_instance_count: int = 1
    model_artifact_s3: Optional[str] = None
    enable_data_capture: bool = True


def create_sagemaker_endpoint(config: SageMakerDeploymentConfig) -> None:
    sm_client = boto3.client("sagemaker")

    model_primary_container = {
        "ModelPackageName": config.model_package_name,
    }

    if config.model_artifact_s3:
        model_primary_container = {
            "Image": config.model_package_name,
            "ModelDataUrl": config.model_artifact_s3,
        }

    model_name = f"{config.endpoint_name}-model"
    sm_client.create_model(
        ModelName=model_name,
        ExecutionRoleArn=config.execution_role_arn,
        PrimaryContainer=model_primary_container,
    )

    endpoint_config_name = f"{config.endpoint_name}-config"
    production_variants = [
        {
            "VariantName": "AllTraffic",
            "ModelName": model_name,
            "InitialInstanceCount": config.initial_instance_count,
            "InstanceType": config.instance_type,
            "InitialVariantWeight": 1.0,
        }
    ]

    data_capture_config = None
    if config.enable_data_capture:
        data_capture_config = {
            "EnableCapture": True,
            "InitialSamplingPercentage": 100,
            "DestinationS3Uri": f"s3://{config.endpoint_name}-monitoring",
            "CaptureOptions": [{"CaptureMode": "Input"}, {"CaptureMode": "Output"}],
        }

    sm_client.create_endpoint_config(
        EndpointConfigName=endpoint_config_name,
        ProductionVariants=production_variants,
        DataCaptureConfig=data_capture_config,
    )

    sm_client.create_endpoint(
        EndpointName=config.endpoint_name,
        EndpointConfigName=endpoint_config_name,
    )


