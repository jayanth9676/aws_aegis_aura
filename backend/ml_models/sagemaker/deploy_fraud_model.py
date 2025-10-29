"""
Deploy fraud detection model to SageMaker endpoint
"""

import os
import boto3
import sagemaker
from sagemaker.sklearn.model import SKLearnModel
from datetime import datetime

# AWS configuration
REGION = os.getenv('AWS_REGION', 'us-east-1')
ROLE = os.getenv('SAGEMAKER_ROLE')  # SageMaker execution role ARN
MODEL_BUCKET = os.getenv('MODEL_BUCKET', 'aegis-ml-models')

def deploy_fraud_detection_model():
    """
    Deploy the fraud detection ensemble model to SageMaker.
    """
    
    print("🚀 Starting fraud detection model deployment...")
    
    # Initialize SageMaker session
    sagemaker_session = sagemaker.Session(boto_session=boto3.Session(region_name=REGION))
    
    # Model artifacts S3 path
    model_artifact_path = f's3://{MODEL_BUCKET}/models/fraud_detector/model.tar.gz'
    
    print(f"📦 Model artifacts: {model_artifact_path}")
    
    # Create SKLearn Model
    sklearn_model = SKLearnModel(
        model_data=model_artifact_path,
        role=ROLE,
        entry_point='inference.py',
        source_dir='./fraud_detector',
        framework_version='1.2-1',
        py_version='py3',
        sagemaker_session=sagemaker_session,
        name=f'aegis-fraud-detector-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    )
    
    print("🔧 Deploying model to endpoint...")
    
    # Deploy to endpoint
    predictor = sklearn_model.deploy(
        initial_instance_count=1,
        instance_type='ml.m5.large',  # Can upgrade to ml.c5.xlarge for production
        endpoint_name='aegis-fraud-detector-endpoint',
        wait=True
    )
    
    print("✅ Model deployed successfully!")
    print(f"📍 Endpoint: {predictor.endpoint_name}")
    
    # Test the endpoint
    print("\n🧪 Testing endpoint...")
    test_features = [
        0.5,  # velocity_score
        1,    # new_payee
        50000,  # amount
        0.3,  # anomaly_score
        0.7,  # mule_risk
        1,    # active_call
        0.2,  # device_risk
        0,    # is_weekend
        1     # is_night
    ]
    
    response = predictor.predict(test_features)
    print(f"✅ Test prediction: {response}")
    
    return predictor.endpoint_name


def deploy_behavioral_model():
    """Deploy behavioral analysis model to SageMaker."""
    
    print("\n🚀 Starting behavioral model deployment...")
    
    sagemaker_session = sagemaker.Session(boto_session=boto3.Session(region_name=REGION))
    
    model_artifact_path = f's3://{MODEL_BUCKET}/models/behavioral/model.tar.gz'
    
    sklearn_model = SKLearnModel(
        model_data=model_artifact_path,
        role=ROLE,
        entry_point='inference.py',
        source_dir='./behavioral',
        framework_version='1.2-1',
        py_version='py3',
        sagemaker_session=sagemaker_session,
        name=f'aegis-behavioral-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    )
    
    predictor = sklearn_model.deploy(
        initial_instance_count=1,
        instance_type='ml.m5.large',
        endpoint_name='aegis-behavioral-endpoint',
        wait=True
    )
    
    print("✅ Behavioral model deployed!")
    print(f"📍 Endpoint: {predictor.endpoint_name}")
    
    return predictor.endpoint_name


def deploy_gnn_mule_model():
    """Deploy GNN mule detection model to SageMaker."""
    
    print("\n🚀 Starting GNN mule detection deployment...")
    
    # GNN model requires PyTorch
    from sagemaker.pytorch.model import PyTorchModel
    
    sagemaker_session = sagemaker.Session(boto_session=boto3.Session(region_name=REGION))
    
    model_artifact_path = f's3://{MODEL_BUCKET}/models/gnn_mule/model.tar.gz'
    
    pytorch_model = PyTorchModel(
        model_data=model_artifact_path,
        role=ROLE,
        entry_point='inference.py',
        source_dir='./gnn_mule',
        framework_version='2.0.0',
        py_version='py310',
        sagemaker_session=sagemaker_session,
        name=f'aegis-gnn-mule-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    )
    
    predictor = pytorch_model.deploy(
        initial_instance_count=1,
        instance_type='ml.m5.xlarge',  # GNN needs more compute
        endpoint_name='aegis-gnn-mule-endpoint',
        wait=True
    )
    
    print("✅ GNN mule model deployed!")
    print(f"📍 Endpoint: {predictor.endpoint_name}")
    
    return predictor.endpoint_name


def update_environment_variables(endpoints: dict):
    """Update backend config with endpoint names."""
    
    print("\n📝 Updating environment variables...")
    
    env_content = f"""
# SageMaker Endpoints
FRAUD_DETECTOR_ENDPOINT={endpoints['fraud']}
BEHAVIORAL_ENDPOINT={endpoints['behavioral']}
GNN_MULE_ENDPOINT={endpoints['gnn']}

# Model configuration
USE_SAGEMAKER=true
MODEL_BUCKET={MODEL_BUCKET}
"""
    
    with open('.env.sagemaker', 'w') as f:
        f.write(env_content)
    
    print("✅ Environment variables written to .env.sagemaker")
    print("   Add these to your .env file or AWS Parameter Store")


def cleanup_old_endpoints():
    """Delete old endpoints to save costs."""
    
    print("\n🧹 Checking for old endpoints to cleanup...")
    
    sagemaker_client = boto3.client('sagemaker', region_name=REGION)
    
    response = sagemaker_client.list_endpoints(
        SortBy='CreationTime',
        SortOrder='Descending',
        NameContains='aegis-'
    )
    
    current_endpoints = {
        'aegis-fraud-detector-endpoint',
        'aegis-behavioral-endpoint',
        'aegis-gnn-mule-endpoint'
    }
    
    for endpoint in response['Endpoints']:
        if endpoint['EndpointName'] not in current_endpoints:
            print(f"🗑️  Deleting old endpoint: {endpoint['EndpointName']}")
            try:
                sagemaker_client.delete_endpoint(
                    EndpointName=endpoint['EndpointName']
                )
            except Exception as e:
                print(f"⚠️  Failed to delete {endpoint['EndpointName']}: {e}")


def main():
    """Main deployment function."""
    
    print("=" * 60)
    print("AEGIS ML MODEL DEPLOYMENT TO SAGEMAKER")
    print("=" * 60)
    
    # Check prerequisites
    if not ROLE:
        print("❌ Error: SAGEMAKER_ROLE environment variable not set")
        print("   Create a SageMaker execution role and set:")
        print("   export SAGEMAKER_ROLE=arn:aws:iam::ACCOUNT:role/SageMakerRole")
        return
    
    print(f"\n📍 Region: {REGION}")
    print(f"🔐 Role: {ROLE}")
    print(f"📦 Model Bucket: {MODEL_BUCKET}")
    
    endpoints = {}
    
    try:
        # Deploy models
        endpoints['fraud'] = deploy_fraud_detection_model()
        endpoints['behavioral'] = deploy_behavioral_model()
        endpoints['gnn'] = deploy_gnn_mule_model()
        
        # Update config
        update_environment_variables(endpoints)
        
        # Cleanup old endpoints
        cleanup_old_endpoints()
        
        print("\n" + "=" * 60)
        print("✅ ALL MODELS DEPLOYED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📋 Deployed endpoints:")
        for model_type, endpoint in endpoints.items():
            print(f"  - {model_type}: {endpoint}")
        
        print("\n📝 Next steps:")
        print("  1. Add .env.sagemaker variables to your .env file")
        print("  2. Update backend/config/system_config.py with endpoint names")
        print("  3. Restart backend: uvicorn api.main:app --reload")
        print("  4. Test with: POST /api/v1/transactions/submit")
        
        print("\n💰 Cost estimate:")
        print("  - ml.m5.large: ~$0.115/hour (fraud + behavioral)")
        print("  - ml.m5.xlarge: ~$0.23/hour (GNN)")
        print("  - Total: ~$0.46/hour (~$330/month for 24/7)")
        print("  💡 Consider using Inference Recommender for cost optimization")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        print("   Check CloudWatch logs for details")
        raise


if __name__ == '__main__':
    main()

