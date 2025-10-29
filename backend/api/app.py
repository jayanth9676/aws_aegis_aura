"""FastAPI application for Aegis Fraud Prevention Platform with AgentCore Runtime."""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional

from agentcore_app import get_aegis_app, shutdown_aegis_app
from utils import get_logger
from graph_db.client import Neo4jClient

logger = get_logger(__name__)


# Pydantic models for API requests/responses
class TransactionRequest(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    payee_account: str
    payment_channel: str
    timestamp: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    behavioral_signals: Optional[Dict] = None


class InvestigationResponse(BaseModel):
    success: bool
    transaction_id: str
    decision: str
    risk_score: Optional[float] = None
    reason_codes: Optional[List[str]] = None
    evidence: Optional[Dict] = None
    error: Optional[str] = None


class DialogueRequest(BaseModel):
    transaction_id: str
    transaction_data: Dict
    risk_factors: List[str]


class DialogueResponse(BaseModel):
    success: bool
    message: str
    assessment: Optional[Dict] = None
    error: Optional[str] = None


class IntelligenceRequest(BaseModel):
    query: str


class IntelligenceResponse(BaseModel):
    success: bool
    documents: List[Dict]
    query: str
    error: Optional[str] = None


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Aegis AgentCore application...")
    
    # Initialize AgentCore app
    aegis_app = await get_aegis_app()
    
    # Test Neo4j connectivity
    try:
        neo4j_client = Neo4jClient()
        if neo4j_client.verify_connectivity():
            logger.info("Neo4j connection verified")
        else:
            logger.warning("Neo4j connection failed - graph features may not work")
        neo4j_client.close()
    except Exception as e:
        logger.warning(f"Neo4j connection test failed: {e}")
    
    logger.info("Aegis application ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Aegis application...")
    await shutdown_aegis_app()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Aegis Fraud Prevention Platform",
    description="AgentCore Runtime-powered fraud prevention system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Aegis Fraud Prevention Platform",
        "version": "1.0.0",
        "agentcore": "enabled"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    aegis_app = await get_aegis_app()
    
    return {
        "status": "healthy",
        "agents_registered": len(aegis_app.agents),
        "runtime": "agentcore",
        "memory": "active",
        "gateway": "active"
    }


@app.post("/api/v1/transactions/investigate", response_model=InvestigationResponse)
async def investigate_transaction(request: TransactionRequest):
    """Investigate a transaction for fraud."""
    try:
        aegis_app = await get_aegis_app()
        
        transaction_data = request.dict()
        result = await aegis_app.investigate_transaction(transaction_data)
        
        return InvestigationResponse(
            success=result.get('success', True),
            transaction_id=request.transaction_id,
            decision=result.get('decision', 'ALLOW'),
            risk_score=result.get('risk_score'),
            reason_codes=result.get('reason_codes', []),
            evidence=result.get('evidence'),
            error=result.get('error')
        )
    except Exception as e:
        logger.error(f"Investigation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/dialogue/engage", response_model=DialogueResponse)
async def engage_customer(request: DialogueRequest):
    """Engage customer with dialogue agent."""
    try:
        aegis_app = await get_aegis_app()
        
        result = await aegis_app.engage_customer(
            request.transaction_data,
            request.risk_factors
        )
        
        return DialogueResponse(
            success=result.get('success', True),
            message=result.get('message', ''),
            assessment=result.get('assessment'),
            error=result.get('error')
        )
    except Exception as e:
        logger.error(f"Customer engagement failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/intelligence/query", response_model=IntelligenceResponse)
async def query_intelligence(request: IntelligenceRequest):
    """Query fraud intelligence knowledge base."""
    try:
        aegis_app = await get_aegis_app()
        
        result = await aegis_app.query_intelligence(request.query)
        
        return IntelligenceResponse(
            success=result.get('success', True),
            documents=result.get('documents', []),
            query=request.query,
            error=result.get('error')
        )
    except Exception as e:
        logger.error(f"Intelligence query failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agents")
async def list_agents():
    """List all registered agents."""
    aegis_app = await get_aegis_app()
    
    return {
        "agents": list(aegis_app.agents.keys()),
        "count": len(aegis_app.agents)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

