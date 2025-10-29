"""CloudWatch metrics tracking for Aegis platform."""

import time
from functools import wraps
from typing import Callable, Any
from config.aws_config import aws_config

class MetricsTracker:
    """Track and publish metrics to CloudWatch."""
    
    def __init__(self, namespace: str = 'Aegis'):
        self.namespace = namespace
        self.cloudwatch = aws_config.cloudwatch
    
    def put_metric(self, metric_name: str, value: float, unit: str = 'None', dimensions: dict = None):
        """Publish a metric to CloudWatch."""
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': time.time()
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
            print(f"Failed to publish metric {metric_name}: {e}")
    
    def track_latency(self, operation: str):
        """Decorator to track operation latency."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    latency_ms = (time.time() - start_time) * 1000
                    self.put_metric(
                        f'{operation}_latency',
                        latency_ms,
                        'Milliseconds',
                        {'operation': operation}
                    )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    latency_ms = (time.time() - start_time) * 1000
                    self.put_metric(
                        f'{operation}_latency',
                        latency_ms,
                        'Milliseconds',
                        {'operation': operation}
                    )
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def track_fraud_detection(self, detected: bool, risk_score: float):
        """Track fraud detection metrics."""
        self.put_metric('FraudDetected', 1 if detected else 0, 'Count')
        self.put_metric('RiskScore', risk_score, 'None')
        self.put_metric('TransactionsAnalyzed', 1, 'Count')
    
    def track_model_performance(self, model_name: str, accuracy: float, fpr: float):
        """Track ML model performance."""
        self.put_metric(
            'ModelAccuracy',
            accuracy,
            'Percent',
            {'model': model_name}
        )
        self.put_metric(
            'FalsePositiveRate',
            fpr,
            'Percent',
            {'model': model_name}
        )
    
    def track_agent_performance(self, agent_name: str, success: bool, latency_ms: float):
        """Track agent execution metrics."""
        self.put_metric(
            f'Agent_{agent_name}_Success',
            1 if success else 0,
            'Count',
            {'agent': agent_name}
        )
        self.put_metric(
            f'Agent_{agent_name}_Latency',
            latency_ms,
            'Milliseconds',
            {'agent': agent_name}
        )

# Global metrics tracker
metrics_tracker = MetricsTracker()



