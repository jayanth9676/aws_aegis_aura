"""AgentCore Observability Configuration - CloudWatch, X-Ray, OpenTelemetry."""

import os
from typing import Optional
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

# Configure X-Ray
xray_recorder.configure(
    service='Aegis-Fraud-Prevention',
    sampling=True,
    context_missing='LOG_ERROR'
)

# Patch AWS SDK and HTTP libraries for automatic tracing
patch_all()


class ObservabilityConfig:
    """Configuration for AgentCore Observability."""
    
    def __init__(self):
        # CloudWatch Configuration
        self.CLOUDWATCH_LOG_GROUP = os.getenv('CLOUDWATCH_LOG_GROUP', '/aegis/agents')
        self.CLOUDWATCH_METRICS_NAMESPACE = os.getenv('CLOUDWATCH_METRICS_NAMESPACE', 'Aegis')
        self.CLOUDWATCH_REGION = os.getenv('AWS_REGION', 'us-east-1')
        
        # X-Ray Configuration
        self.XRAY_ENABLED = os.getenv('XRAY_ENABLED', 'true').lower() == 'true'
        self.XRAY_SAMPLING_RATE = float(os.getenv('XRAY_SAMPLING_RATE', '0.1'))
        
        # OpenTelemetry Configuration
        self.OTEL_ENABLED = os.getenv('OTEL_ENABLED', 'false').lower() == 'true'
        self.OTEL_ENDPOINT = os.getenv('OTEL_ENDPOINT', '')
        
        # Metrics Configuration
        self.METRICS_ENABLED = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
        self.METRICS_FLUSH_INTERVAL = int(os.getenv('METRICS_FLUSH_INTERVAL', '60'))
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.STRUCTURED_LOGGING = os.getenv('STRUCTURED_LOGGING', 'true').lower() == 'true'
    
    def get_cloudwatch_config(self) -> dict:
        """Get CloudWatch configuration."""
        return {
            'log_group': self.CLOUDWATCH_LOG_GROUP,
            'metrics_namespace': self.CLOUDWATCH_METRICS_NAMESPACE,
            'region': self.CLOUDWATCH_REGION
        }
    
    def get_xray_config(self) -> dict:
        """Get X-Ray configuration."""
        return {
            'enabled': self.XRAY_ENABLED,
            'sampling_rate': self.XRAY_SAMPLING_RATE,
            'service_name': 'Aegis-Fraud-Prevention'
        }
    
    def get_metrics_config(self) -> dict:
        """Get metrics configuration."""
        return {
            'enabled': self.METRICS_ENABLED,
            'namespace': self.CLOUDWATCH_METRICS_NAMESPACE,
            'flush_interval': self.METRICS_FLUSH_INTERVAL
        }


# Global observability config
observability_config = ObservabilityConfig()


# CloudWatch Metrics Helper
import boto3
from datetime import datetime

class CloudWatchMetrics:
    """Helper class for CloudWatch metrics."""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch', region_name=observability_config.CLOUDWATCH_REGION)
        self.namespace = observability_config.CLOUDWATCH_METRICS_NAMESPACE
    
    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = 'None',
        dimensions: Optional[dict] = None
    ):
        """Put a metric to CloudWatch."""
        if not observability_config.METRICS_ENABLED:
            return
        
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
        except Exception as e:
            print(f"Failed to put metric: {e}")
    
    def track_agent_invocation(
        self,
        agent_name: str,
        success: bool,
        latency_ms: float
    ):
        """Track agent invocation metrics."""
        dimensions = {'AgentName': agent_name}
        
        # Invocation count
        self.put_metric('AgentInvocations', 1.0, 'Count', dimensions)
        
        # Success/failure count
        if success:
            self.put_metric('AgentSuccess', 1.0, 'Count', dimensions)
        else:
            self.put_metric('AgentErrors', 1.0, 'Count', dimensions)
        
        # Latency
        self.put_metric('AgentLatency', latency_ms, 'Milliseconds', dimensions)
    
    def track_fraud_decision(
        self,
        decision: str,
        risk_score: float,
        model_name: Optional[str] = None
    ):
        """Track fraud decision metrics."""
        dimensions = {'Decision': decision}
        if model_name:
            dimensions['ModelName'] = model_name
        
        # Decision count
        self.put_metric('FraudDecisions', 1.0, 'Count', dimensions)
        
        # Risk score
        self.put_metric('RiskScore', risk_score, 'None', dimensions)
    
    def track_tool_invocation(
        self,
        tool_name: str,
        success: bool,
        latency_ms: float
    ):
        """Track tool invocation metrics."""
        dimensions = {'ToolName': tool_name}
        
        # Tool invocation count
        self.put_metric('ToolInvocations', 1.0, 'Count', dimensions)
        
        # Success/failure
        if success:
            self.put_metric('ToolSuccess', 1.0, 'Count', dimensions)
        else:
            self.put_metric('ToolErrors', 1.0, 'Count', dimensions)
        
        # Latency
        self.put_metric('ToolLatency', latency_ms, 'Milliseconds', dimensions)


# Global metrics instance
cloudwatch_metrics = CloudWatchMetrics()

