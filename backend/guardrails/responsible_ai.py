"""Responsible AI module for bias detection and fairness monitoring."""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
from collections import defaultdict

from config import aws_config, system_config
from utils import get_logger

logger = get_logger(__name__)


class BiasDetectionModule:
    """Bias detection and fairness monitoring for fraud detection system."""
    
    def __init__(self):
        """Initialize bias detection module."""
        self.cloudwatch = aws_config.cloudwatch
        self.dynamodb = aws_config.dynamodb
        self.protected_attributes = ['age', 'gender', 'race', 'location', 'income_band']
        self.disparate_impact_threshold = 0.20  # 20% threshold per constitution
    
    async def detect_bias(
        self,
        predictions: List[Dict],
        customer_attributes: List[Dict]
    ) -> Dict:
        """Detect bias in fraud predictions across demographic groups.
        
        Args:
            predictions: List of fraud decisions
            customer_attributes: List of customer demographic attributes
            
        Returns:
            Dict with bias detection results
        """
        try:
            # Calculate false positive rate by demographic group
            fpr_by_group = self._calculate_fpr_by_group(predictions, customer_attributes)
            
            # Check for disparate impact
            bias_detected, violations = self._check_disparate_impact(fpr_by_group)
            
            # Publish metrics to CloudWatch
            await self._publish_bias_metrics(fpr_by_group)
            
            # Trigger alerts if bias detected
            if bias_detected:
                await self._trigger_bias_alert(violations)
            
            return {
                'bias_detected': bias_detected,
                'fpr_by_group': fpr_by_group,
                'violations': violations,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Bias detection failed", error=str(e))
            return {
                'bias_detected': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _calculate_fpr_by_group(
        self,
        predictions: List[Dict],
        customer_attributes: List[Dict]
    ) -> Dict[str, Dict]:
        """Calculate false positive rate by demographic group.
        
        Args:
            predictions: List of fraud decisions
            customer_attributes: List of customer attributes
            
        Returns:
            Dict mapping group to FPR statistics
        """
        # Group predictions by demographic attributes
        groups = defaultdict(lambda: {
            'total': 0,
            'false_positives': 0,
            'true_positives': 0,
            'false_negatives': 0,
            'true_negatives': 0
        })
        
        for pred, attrs in zip(predictions, customer_attributes):
            predicted_fraud = pred.get('decision') in ['BLOCK', 'CHALLENGE']
            actual_fraud = pred.get('actual_label', False)  # Ground truth if available
            
            # If we don't have ground truth, skip FPR calculation
            if 'actual_label' not in pred:
                continue
            
            # Categorize prediction
            if predicted_fraud and not actual_fraud:
                outcome = 'false_positives'
            elif predicted_fraud and actual_fraud:
                outcome = 'true_positives'
            elif not predicted_fraud and actual_fraud:
                outcome = 'false_negatives'
            else:
                outcome = 'true_negatives'
            
            # Group by each protected attribute
            for attr in self.protected_attributes:
                if attr in attrs:
                    group_key = f"{attr}_{attrs[attr]}"
                    groups[group_key]['total'] += 1
                    groups[group_key][outcome] += 1
        
        # Calculate FPR for each group
        fpr_by_group = {}
        for group, stats in groups.items():
            total_negatives = stats['false_positives'] + stats['true_negatives']
            if total_negatives > 0:
                fpr = stats['false_positives'] / total_negatives
            else:
                fpr = 0.0
            
            fpr_by_group[group] = {
                'fpr': fpr,
                'false_positives': stats['false_positives'],
                'true_negatives': stats['true_negatives'],
                'total': stats['total']
            }
        
        return fpr_by_group
    
    def _check_disparate_impact(
        self,
        fpr_by_group: Dict[str, Dict]
    ) -> tuple[bool, List[Dict]]:
        """Check for disparate impact across groups.
        
        Uses the 80% rule: ratio of FPR between any two groups should be >= 0.8
        or <= 1.2 (i.e., within 20% of each other).
        
        Args:
            fpr_by_group: FPR statistics by group
            
        Returns:
            Tuple of (bias_detected, list of violations)
        """
        violations = []
        
        # Group FPRs by attribute type
        fprs_by_attribute = defaultdict(dict)
        for group_key, stats in fpr_by_group.items():
            attr_type = group_key.rsplit('_', 1)[0]  # e.g., "age" from "age_25-35"
            fprs_by_attribute[attr_type][group_key] = stats['fpr']
        
        # Check disparate impact within each attribute
        for attr_type, group_fprs in fprs_by_attribute.items():
            if len(group_fprs) < 2:
                continue
            
            # Find min and max FPR
            min_fpr = min(group_fprs.values())
            max_fpr = max(group_fprs.values())
            
            # Calculate disparate impact ratio
            if min_fpr > 0:
                di_ratio = max_fpr / min_fpr
            else:
                di_ratio = float('inf') if max_fpr > 0 else 1.0
            
            # Check if exceeds threshold (20% = ratio of 1.2)
            if di_ratio > (1 + self.disparate_impact_threshold):
                violations.append({
                    'attribute': attr_type,
                    'max_fpr': max_fpr,
                    'min_fpr': min_fpr,
                    'di_ratio': di_ratio,
                    'threshold_exceeded': True,
                    'groups': group_fprs
                })
        
        bias_detected = len(violations) > 0
        return bias_detected, violations
    
    async def _publish_bias_metrics(self, fpr_by_group: Dict[str, Dict]):
        """Publish bias metrics to CloudWatch.
        
        Args:
            fpr_by_group: FPR statistics by group
        """
        try:
            metric_data = []
            
            for group, stats in fpr_by_group.items():
                metric_data.append({
                    'MetricName': f'FalsePositiveRate_{group}',
                    'Value': stats['fpr'],
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow()
                })
            
            # Publish in batches of 20 (CloudWatch limit)
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i:i+20]
                self.cloudwatch.put_metric_data(
                    Namespace='Aegis/ResponsibleAI',
                    MetricData=batch
                )
            
            logger.info(f"Published {len(metric_data)} bias metrics to CloudWatch")
            
        except Exception as e:
            logger.error(f"Failed to publish bias metrics", error=str(e))
    
    async def _trigger_bias_alert(self, violations: List[Dict]):
        """Trigger alerts for detected bias.
        
        Args:
            violations: List of bias violations
        """
        try:
            # Log alert
            logger.warning(
                "BIAS DETECTED - Disparate impact threshold exceeded",
                violations=violations
            )
            
            # Publish SNS notification (if configured)
            sns_topic = os.getenv('BIAS_ALERT_TOPIC_ARN')
            if sns_topic:
                sns = aws_config.eventbridge
                message = {
                    'alert_type': 'BIAS_DETECTED',
                    'timestamp': datetime.utcnow().isoformat(),
                    'violations': violations,
                    'severity': 'HIGH',
                    'action_required': 'Review model fairness and retrain if necessary'
                }
                
                # Note: In production, use SNS client properly
                logger.info(f"Would publish bias alert to SNS", topic=sns_topic)
            
        except Exception as e:
            logger.error(f"Failed to trigger bias alert", error=str(e))
    
    async def generate_fairness_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Generate fairness report for date range.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Fairness report dict
        """
        try:
            # Query decisions from DynamoDB
            decisions_table = self.dynamodb.Table(system_config.TRANSACTIONS_TABLE)
            
            # Scan for decisions in date range
            # In production, use GSI for efficient querying
            response = decisions_table.scan(
                FilterExpression='created_at BETWEEN :start AND :end',
                ExpressionAttributeValues={
                    ':start': start_date.isoformat(),
                    ':end': end_date.isoformat()
                }
            )
            
            decisions = response.get('Items', [])
            
            # Get customer attributes
            customers_table = self.dynamodb.Table(system_config.CUSTOMERS_TABLE)
            customer_attributes = []
            
            for decision in decisions:
                customer_id = decision.get('customer_id')
                if customer_id:
                    customer_response = customers_table.get_item(Key={'customer_id': customer_id})
                    if 'Item' in customer_response:
                        customer_attributes.append(customer_response['Item'])
            
            # Calculate bias metrics
            bias_result = await self.detect_bias(decisions, customer_attributes)
            
            report = {
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'total_decisions': len(decisions),
                'bias_detected': bias_result['bias_detected'],
                'fpr_by_group': bias_result['fpr_by_group'],
                'violations': bias_result.get('violations', []),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate fairness report", error=str(e))
            return {
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }


# Global bias detection module instance
_bias_detector = None


def get_bias_detector() -> BiasDetectionModule:
    """Get global bias detector instance."""
    global _bias_detector
    if _bias_detector is None:
        _bias_detector = BiasDetectionModule()
    return _bias_detector


async def check_bias(predictions: List[Dict], customer_attributes: List[Dict]) -> Dict:
    """Check for bias in predictions.
    
    Convenience function that uses global bias detector instance.
    
    Args:
        predictions: List of fraud decisions
        customer_attributes: List of customer attributes
        
    Returns:
        Bias detection results
    """
    detector = get_bias_detector()
    return await detector.detect_bias(predictions, customer_attributes)

