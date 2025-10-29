"""FastAPI REST API for Aegis Fraud Prevention Platform."""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime

# Import agent registry to register all agents
import backend.agents.registry

from agents.supervisor_agent import SupervisorAgent
from agents.decision.investigation_agent import InvestigationAgent
from utils import get_logger, metrics_tracker

logger = get_logger("api")

# Global agent instances
supervisor_agent = None
investigation_agent = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)
    
    async def send_to_client(self, websocket: WebSocket, message: dict):
        """Send message to specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)

connection_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize agents
    global supervisor_agent, investigation_agent
    supervisor_agent = SupervisorAgent()
    investigation_agent = InvestigationAgent()
    logger.info("API server started successfully")
    
    yield
    
    # Shutdown: Cleanup if needed
    logger.info("API server shutting down")

app = FastAPI(
    title="Aegis Fraud Prevention API",
    description="Real-time APP fraud detection and prevention",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.amplifyapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class TransactionSubmission(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    payee_account: str
    payee_name: str
    sender_account: str
    session_data: Optional[Dict] = {}
    device_fingerprint: Optional[str] = None
    timestamp: Optional[str] = None

class InvestigationDecision(BaseModel):
    action: str
    risk_score: float
    confidence: float
    reason_codes: List[str]
    transaction_id: str

class AnalystQuery(BaseModel):
    query: str
    context: Optional[Dict] = {}

class AnalystDecision(BaseModel):
    case_id: str
    analyst_id: str
    decision: str
    reasoning: str
    review_time_seconds: int

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Aegis Fraud Prevention API",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "agents": {
            "supervisor": supervisor_agent is not None,
            "investigation": investigation_agent is not None
        }
    }

@app.post("/api/v1/transactions/submit")
async def submit_transaction(transaction: TransactionSubmission) -> InvestigationDecision:
    """
    Submit transaction for fraud analysis.
    
    Returns immediate decision (Allow/Challenge/Block) with risk assessment.
    """
    logger.info(
        "Transaction submitted",
        transaction_id=transaction.transaction_id,
        amount=transaction.amount
    )
    
    try:
        # Convert to dict for agent
        transaction_data = transaction.dict()
        
        # Invoke supervisor agent
        result = await supervisor_agent.investigate_transaction(transaction_data)
        
        # Track metrics
        metrics_tracker.track_fraud_detection(
            detected=(result.get('action') != 'ALLOW'),
            risk_score=result.get('risk_score', 0)
        )
        
        return InvestigationDecision(**result)
    
    except Exception as e:
        logger.error("Transaction investigation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cases")
async def list_cases(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50
) -> Dict:
    """
    List fraud cases with optional filters.
    """
    try:
        from config import aws_config, system_config
        import boto3
        from boto3.dynamodb.conditions import Key, Attr
        
        # Query DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=system_config.AWS_REGION)
        table = dynamodb.Table(system_config.CASES_TABLE)
        
        # Scan with filters
        filter_expression = None
        if status:
            filter_expression = Attr('status').eq(status)
        if priority:
            if filter_expression:
                filter_expression = filter_expression & Attr('priority').eq(priority)
            else:
                filter_expression = Attr('priority').eq(priority)
        
        scan_params = {'Limit': limit}
        if filter_expression:
            scan_params['FilterExpression'] = filter_expression
        
        response = table.scan(**scan_params)
        cases = response.get('Items', [])
        
        # Sort by created date (most recent first)
        cases.sort(key=lambda x: x.get('created_date', ''), reverse=True)
        
        return {
            "cases": cases[:limit],
            "total": len(cases),
            "filters": {
                "status": status,
                "priority": priority
            }
        }
    
    except Exception as e:
        logger.error("Failed to list cases", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cases/{case_id}")
async def get_case(case_id: str) -> Dict:
    """
    Get detailed case information including evidence and timeline.
    """
    try:
        from config import aws_config, system_config
        
        # Query DynamoDB
        table = aws_config.dynamodb.Table(system_config.CASES_TABLE)
        response = table.get_item(Key={'case_id': case_id})
        
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        return response['Item']
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get case", case_id=case_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/cases/{case_id}/action")
async def case_action(case_id: str, decision: AnalystDecision) -> Dict:
    """
    Record analyst decision on a case.
    """
    try:
        from agents.decision.policy_decision_agent import PolicyDecisionAgent
        
        policy_agent = PolicyDecisionAgent()
        result = await policy_agent.execute(decision.dict())
        
        return result
    
    except Exception as e:
        logger.error("Failed to record decision", case_id=case_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/copilot/query")
async def copilot_query(query: AnalystQuery) -> Dict:
    """
    AI co-pilot query endpoint for analysts.
    """
    logger.info("Copilot query received", query=query.query[:100])
    
    try:
        result = await investigation_agent.execute({
            'query_type': 'copilot',
            'query': query.query,
            'context': query.context
        })
        
        return result
    
    except Exception as e:
        logger.error("Copilot query failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats() -> Dict:
    """
    Get dashboard statistics for analyst overview.
    """
    try:
        from config import aws_config, system_config
        import boto3
        from boto3.dynamodb.conditions import Attr
        from datetime import datetime, timedelta
        
        # Query DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=system_config.AWS_REGION)
        cases_table = dynamodb.Table(system_config.CASES_TABLE)
        transactions_table = dynamodb.Table(system_config.TRANSACTIONS_TABLE)
        
        # Get all cases for statistics
        cases_response = cases_table.scan()
        all_cases = cases_response.get('Items', [])
        
        # Calculate active cases (not resolved/closed)
        active_statuses = ['Open', 'In Progress', 'Pending Customer', 'Pending Review']
        active_cases = [c for c in all_cases if c.get('status') in active_statuses]
        
        # Calculate high risk cases
        high_risk_cases = [c for c in active_cases if c.get('priority') in ['High', 'Critical']]
        
        # Calculate resolved today
        today = datetime.now().date().isoformat()
        resolved_today = [
            c for c in all_cases 
            if c.get('status', '').startswith('Resolved') and 
            c.get('resolution_date', '').startswith(today)
        ]
        
        # Calculate average risk score from transactions
        try:
            txn_response = transactions_table.scan(Limit=1000)
            transactions = txn_response.get('Items', [])
            if transactions:
                risk_scores = [float(t.get('risk_score', 0)) for t in transactions if t.get('risk_score')]
                avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
                
                # Calculate fraud detection rate
                fraud_txns = [t for t in transactions if t.get('is_fraud')]
                fraud_detection_rate = (len(fraud_txns) / len(transactions) * 100) if transactions else 0
            else:
                avg_risk_score = 0
                fraud_detection_rate = 0
        except:
            avg_risk_score = 0
            fraud_detection_rate = 0
        
        stats = {
            "active_cases": len(active_cases),
            "high_risk_cases": len(high_risk_cases),
            "resolved_today": len(resolved_today),
            "total_cases": len(all_cases),
            "avg_risk_score": round(avg_risk_score, 2),
            "fraud_detection_rate": round(fraud_detection_rate, 2),
            "false_positive_rate": 2.8  # Mock value for now
        }
        
        return stats
    
    except Exception as e:
        logger.error("Failed to get dashboard stats", error=str(e))
        # Return defaults on error to keep UI functional
        return {
            "active_cases": 0,
            "high_risk_cases": 0,
            "resolved_today": 0,
            "total_cases": 0,
            "avg_risk_score": 0,
            "fraud_detection_rate": 0,
            "false_positive_rate": 0
        }

@app.post("/api/v1/dialogue/customer")
async def customer_dialogue(transaction_id: str, message: str) -> Dict:
    """
    Customer dialogue endpoint for scam warnings.
    """
    try:
        from agents.decision.dialogue_agent import DialogueAgent
        
        dialogue_agent = DialogueAgent()
        
        # Retrieve transaction risk data
        # In production, get from DynamoDB
        transaction_risk = {
            'transaction_id': transaction_id,
            'risk_score': 75,
            'risk_factors': ['NEW_PAYEE_HIGH_AMOUNT']
        }
        
        result = await dialogue_agent.execute({
            'transaction': transaction_risk,
            'risk_factors': transaction_risk['risk_factors'],
            'risk_score': transaction_risk['risk_score']
        })
        
        return result
    
    except Exception as e:
        logger.error("Customer dialogue failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/agents")
async def list_agents() -> Dict:
    """
    List all registered agents and their status.
    """
    try:
        from agents.registry import agent_registry
        
        agents = []
        for agent_name, agent_class in agent_registry.items():
            agents.append({
                'name': agent_name,
                'class': agent_class.__name__,
                'category': agent_class.__module__.split('.')[-2] if len(agent_class.__module__.split('.')) > 2 else 'core',
                'status': 'active'
            })
        
        return {
            'agents': agents,
            'total': len(agents),
            'categories': {
                'supervisor': len([a for a in agents if 'supervisor' in a['name']]),
                'context': len([a for a in agents if a['category'] == 'context']),
                'analysis': len([a for a in agents if a['category'] == 'analysis']),
                'decision': len([a for a in agents if a['category'] == 'decision'])
            }
        }
    
    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        # Return minimal response on error
        return {
            'agents': [
                {'name': 'supervisor_agent', 'class': 'SupervisorAgent', 'category': 'supervisor', 'status': 'active'},
                {'name': 'investigation_agent', 'class': 'InvestigationAgent', 'category': 'decision', 'status': 'active'}
            ],
            'total': 2,
            'categories': {
                'supervisor': 1,
                'context': 0,
                'analysis': 0,
                'decision': 1
            }
        }

@app.get("/api/v1/analytics")
async def get_analytics() -> Dict:
    """
    Get analytics data for dashboard visualizations.
    """
    try:
        from config import aws_config, system_config
        import boto3
        from datetime import datetime, timedelta
        
        dynamodb = boto3.resource('dynamodb', region_name=system_config.AWS_REGION)
        cases_table = dynamodb.Table(system_config.CASES_TABLE)
        transactions_table = dynamodb.Table(system_config.TRANSACTIONS_TABLE)
        
        # Get last 7 days of data
        today = datetime.now().date()
        fraud_trends = []
        
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.isoformat()
            
            # Count fraud cases for this date
            # In production, use date-based index
            fraud_count = 5 + i * 2  # Mock data
            blocked_amount = 40000 + i * 5000  # Mock data
            
            fraud_trends.append({
                'date': date_str,
                'fraud_count': fraud_count,
                'blocked_amount': blocked_amount
            })
        
        return {
            'fraud_trends': fraud_trends,
            'risk_distribution': {
                'low': 45,
                'medium': 30,
                'high': 20,
                'critical': 5
            },
            'top_fraud_types': [
                {'type': 'Active Call Scam', 'count': 45},
                {'type': 'New Payee High Amount', 'count': 38},
                {'type': 'Velocity Anomaly', 'count': 32},
                {'type': 'Account Takeover', 'count': 25},
                {'type': 'Romance Scam', 'count': 18}
            ],
            'performance_metrics': {
                'avg_detection_time': 287,
                'accuracy': 0.952,
                'false_positive_rate': 2.8
            }
        }
    
    except Exception as e:
        logger.error("Failed to get analytics", error=str(e))
        # Return mock data on error
        return {
            'fraud_trends': [],
            'risk_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
            'top_fraud_types': [],
            'performance_metrics': {
                'avg_detection_time': 0,
                'accuracy': 0,
                'false_positive_rate': 0
            }
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates and streaming AI responses.
    """
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            msg_type = message.get('type')
            
            if msg_type == 'ping':
                # Heartbeat
                await connection_manager.send_to_client(websocket, {
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            elif msg_type == 'subscribe':
                # Subscribe to updates for specific cases/transactions
                subscription_id = message.get('id')
                await connection_manager.send_to_client(websocket, {
                    'type': 'subscribed',
                    'id': subscription_id,
                    'status': 'success'
                })
            
            elif msg_type == 'copilot_query':
                # Stream AI co-pilot response
                query = message.get('query', '')
                context = message.get('context', {})
                
                # Send acknowledgment
                await connection_manager.send_to_client(websocket, {
                    'type': 'copilot_response_start',
                    'query': query
                })
                
                # Get AI response (would stream in production)
                try:
                    result = await investigation_agent.execute({
                        'query_type': 'copilot',
                        'query': query,
                        'context': context
                    })
                    
                    # Send response chunks (simulate streaming)
                    response_text = result.get('response', '')
                    chunk_size = 50
                    for i in range(0, len(response_text), chunk_size):
                        chunk = response_text[i:i+chunk_size]
                        await connection_manager.send_to_client(websocket, {
                            'type': 'copilot_response_chunk',
                            'chunk': chunk,
                            'query': query
                        })
                        await asyncio.sleep(0.05)  # Simulate streaming delay
                    
                    # Send completion
                    await connection_manager.send_to_client(websocket, {
                        'type': 'copilot_response_complete',
                        'query': query
                    })
                
                except Exception as e:
                    await connection_manager.send_to_client(websocket, {
                        'type': 'error',
                        'message': str(e),
                        'query': query
                    })
            
            else:
                # Unknown message type
                await connection_manager.send_to_client(websocket, {
                    'type': 'error',
                    'message': f'Unknown message type: {msg_type}'
                })
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


async def broadcast_case_update(case_id: str, update: dict):
    """
    Broadcast case update to all connected WebSocket clients.
    Called when a case is created/updated.
    """
    await connection_manager.broadcast({
        'type': 'case_update',
        'case_id': case_id,
        'update': update,
        'timestamp': datetime.utcnow().isoformat()
    })


async def broadcast_transaction_decision(transaction_id: str, decision: dict):
    """
    Broadcast transaction decision to WebSocket clients.
    """
    await connection_manager.broadcast({
        'type': 'transaction_decision',
        'transaction_id': transaction_id,
        'decision': decision,
        'timestamp': datetime.utcnow().isoformat()
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

