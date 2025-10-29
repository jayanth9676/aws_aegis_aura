"""Create Bedrock Guardrails from JSON configurations."""

import boto3
import json
import os

def create_guardrails():
    """Create Bedrock Guardrails for input and output filtering."""
    
    bedrock = boto3.client('bedrock')
    
    guardrails_dir = 'backend/guardrails'
    
    guardrails = [
        {
            'name': 'input_guardrails.json',
            'description': 'Input guardrails for prompt injection and PII protection'
        },
        {
            'name': 'output_guardrails.json',
            'description': 'Output guardrails for safe customer-facing dialogue'
        }
    ]
    
    print("Creating Bedrock Guardrails...")
    
    for guardrail_info in guardrails:
        config_path = os.path.join(guardrails_dir, guardrail_info['name'])
        
        if not os.path.exists(config_path):
            print(f"✗ Guardrail config not found: {config_path}")
            continue
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"Creating guardrail: {config['name']}")
        print(f"  Description: {guardrail_info['description']}")
        
        # In production, create actual Bedrock Guardrail
        # For now, just validate config
        print(f"  ✓ Config validated: {len(json.dumps(config))} bytes")
        print(f"  Note: Use AWS Console or CDK to create actual Guardrail resource")
    
    print("\n✓ Guardrails configurations ready")
    print("\nTo create actual guardrails:")
    print("  1. Navigate to AWS Bedrock Console")
    print("  2. Go to Guardrails section")
    print("  3. Create new guardrail")
    print("  4. Import configuration from backend/guardrails/*.json")
    print("  5. Copy Guardrail ID to env.template")

if __name__ == '__main__':
    create_guardrails()



