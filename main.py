"""
Aegis Fraud Prevention Platform - Main Entry Point

This is a demonstration of the Aegis platform's agent-based fraud detection.
For production deployment, use the FastAPI server in backend/api/
"""

import asyncio
from backend.agents.supervisor_agent import SupervisorAgent
from backend.utils import get_logger

logger = get_logger("main")

async def test_fraud_investigation():
    """Demonstrate fraud investigation workflow."""
    
    logger.info("Initializing Aegis Supervisor Agent...")
    supervisor = SupervisorAgent()
    
    # Example high-risk transaction
    test_transaction = {
        'transaction_id': 'DEMO-001',
        'customer_id': 'CUST-12345',
        'amount': 8500,
        'payee_account': '98765432',
        'payee_name': 'Unknown Limited',
        'sender_account': '12345678',
        'session_data': {
            'active_call': True,  # Critical fraud indicator!
            'typing_patterns': [],
            'device_fingerprint': 'unknown-device-001'
        },
        'timestamp': '2024-10-15T14:30:00Z',
        'payee_sort_code': '12-34-56'
    }
    
    logger.info("Investigating transaction...", transaction_id=test_transaction['transaction_id'])
    
    # Run investigation
    result = await supervisor.investigate_transaction(test_transaction)
    
    # Display results
    print("\n" + "="*70)
    print("AEGIS FRAUD DETECTION RESULT")
    print("="*70)
    print(f"Transaction ID: {test_transaction['transaction_id']}")
    print(f"Amount: £{test_transaction['amount']:,.2f}")
    print(f"Payee: {test_transaction['payee_name']}")
    print("-"*70)
    print(f"Decision: {result.get('action', 'UNKNOWN')}")
    print(f"Risk Score: {result.get('risk_score', 0):.1f}/100")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print("-"*70)
    print("Risk Factors:")
    for code in result.get('reason_codes', []):
        print(f"  • {code}")
    print("="*70)
    print("\nFor full analysis, check analyst dashboard at http://localhost:3000/analyst")
    print("="*70 + "\n")

def main():
    """Main entry point for Aegis platform demo."""
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     AEGIS - Agentic AI Fraud Prevention Platform            ║
    ║                                                              ║
    ║     Multi-Agent System for APP Fraud Detection              ║
    ║     Built on AWS Bedrock AgentCore                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("Running fraud investigation demo...\n")
    
    try:
        asyncio.run(test_fraud_investigation())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        print("\nNote: For full functionality, ensure AWS credentials are configured")
        print("and required AWS resources are deployed. See QUICK_START_GUIDE.md")

if __name__ == "__main__":
    main()
