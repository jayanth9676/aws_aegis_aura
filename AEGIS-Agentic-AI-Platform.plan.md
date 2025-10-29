# Aegis: Production-Ready Agentic AI Fraud Prevention Platform

## System Overview

Complete AWS Bedrock AgentCore-native multi-agent fraud prevention system with Strands Agents framework, Responsible AI, Explainable AI, and Bedrock Guardrails - production-ready deployment to AWS from day 1.

**Core Technologies:**

- **Agent Framework:** Strands Agents on AWS Bedrock AgentCore Runtime
- **Agent Memory:** AgentCore Memory (short-term sessions + long-term persistence)
- **Tool Integration:** AgentCore Gateway (Lambda, SageMaker, APIs)
- **Security:** AgentCore Identity (Cognito, IAM)
- **Observability:** AgentCore Observability (CloudWatch, X-Ray, OpenTelemetry)
- **AI Models:** Claude 4 Sonnet, Titan Embeddings via Bedrock
- **Guardrails:** Bedrock Guardrails for input/output safety
- **Graph Database:** Amazon Neptune (managed)
- **Vector Store:** Bedrock Knowledge Bases with OpenSearch Serverless
- **Frontend:** Next.js deployed to AWS Amplify

## Phase 1: AWS Infrastructure Setup (Infrastructure as Code)

### 1.1 Project Structure

```
aegis-fraud-prevention/
├── infrastructure/
│   ├── cdk/                          # AWS CDK Infrastructure
│   │   ├── agentcore-stack.ts        # AgentCore Runtime, Memory, Gateway, Identity
│   │   ├── bedrock-stack.ts          # Bedrock models, Knowledge Bases, Guardrails
│   │   ├── ml-inference-stack.ts     # SageMaker endpoints or Lambda ML
│   │   ├── api-stack.ts              # API Gateway, Lambda, AppSync
│   │   ├── database-stack.ts         # DynamoDB, Neptune, S3
│   │   ├── frontend-stack.ts         # Amplify, CloudFront
│   │   ├── security-stack.ts         # Cognito, IAM roles, KMS
│   │   └── observability-stack.ts    # CloudWatch dashboards, X-Ray, alarms
│   └── scripts/
│       ├── deploy.sh                 # Deployment automation
│       └── setup-knowledge-base.py   # KB document upload and indexing
├── backend/
│   ├── agents/                       # Strands Agent implementations
│   │   ├── base_agent.py             # Base class with AgentCore integration
│   │   ├── supervisor_agent.py       # Central orchestrator
│   │   ├── context/                  # Context gathering agents
│   │   │   ├── transaction_context_agent.py
│   │   │   ├── customer_context_agent.py
│   │   │   ├── payee_context_agent.py
│   │   │   ├── behavioral_analysis_agent.py
│   │   │   └── graph_relationship_agent.py
│   │   ├── analysis/                 # Analysis agents
│   │   │   ├── risk_scoring_agent.py
│   │   │   └── intel_agent.py        # RAG agent
│   │   └── decision/                 # Decision & action agents
│   │       ├── triage_agent.py
│   │       ├── dialogue_agent.py     # Customer dialogue with Guardrails
│   │       ├── investigation_agent.py
│   │       ├── policy_decision_agent.py
│   │       └── regulatory_reporting_agent.py
│   ├── tools/                        # AgentCore Gateway tools (Lambda functions)
│   │   ├── payment_tools.py          # Transaction API, payment controls
│   │   ├── verification_tools.py     # CoP, watchlist, sanctions
│   │   ├── customer_tools.py         # Customer data, KYC
│   │   ├── behavioral_tools.py       # Behavioral biometrics
│   │   ├── graph_tools.py            # Neptune graph queries
│   │   ├── ml_model_tools.py         # SageMaker/Lambda ML inference
│   │   ├── knowledge_base_tools.py   # Bedrock KB RAG queries
│   │   ├── dialogue_tools.py         # Dialogue management
│   │   ├── case_management_tools.py  # Case CRUD, escalation
│   │   ├── regulatory_tools.py       # SAR generation, filing
│   │   └── explainability_tools.py   # SHAP, model explanations
│   ├── ml_models/                    # ML model deployment
│   │   ├── sagemaker/                # SageMaker model configs
│   │   │   ├── fraud_detector/       # Ensemble model endpoint
│   │   │   ├── mule_detector/        # GNN model endpoint
│   │   │   ├── behavioral_model/     # Sequence model endpoint
│   │   │   └── anomaly_detector/     # Autoencoder endpoint
│   │   └── lambda/                   # Lambda-based model serving (if no SageMaker)
│   │       ├── fraud_detector.py     # Loads pickles, serves inference
│   │       ├── mule_detector.py
│   │       ├── behavioral_analyzer.py
│   │       └── anomaly_detector.py
│   ├── api/                          # API Gateway Lambda handlers
│   │   ├── transaction_handler.py    # Submit transaction
│   │   ├── case_handler.py           # Case CRUD operations
│   │   ├── dashboard_handler.py      # Analytics and stats
│   │   ├── dialogue_handler.py       # Customer/analyst dialogue
│   │   └── websocket_handler.py      # AppSync real-time subscriptions
│   ├── guardrails/                   # Bedrock Guardrails configurations
│   │   ├── input_guardrails.json     # Prompt injection, PII detection
│   │   ├── output_guardrails.json    # Content filtering, topic denial
│   │   └── responsible_ai.py         # Bias detection, fairness monitoring
│   ├── knowledge_base/
│   │   ├── setup.py                  # KB creation and indexing
│   │   ├── populate.py               # Document upload to S3
│   │   └── rag_client.py             # Query interface
│   ├── graph_db/
│   │   ├── neptune_client.py         # Neptune connection and queries
│   │   ├── schema.py                 # Graph schema definition
│   │   └── mule_detection.py         # GNN-based mule detection logic
│   ├── config/
│   │   ├── aws_config.py             # AWS service clients
│   │   ├── agent_config.py           # Agent configurations
│   │   └── guardrails_config.py      # Guardrails policies
│   └── utils/
│       ├── logging.py                # Structured logging
│       ├── metrics.py                # Custom CloudWatch metrics
│       └── tracing.py                # X-Ray tracing helpers
├── frontend/
│   ├── app/
│   │   ├── analyst/                  # Analyst interface
│   │   │   ├── page.tsx              # Main dashboard
│   │   │   ├── cases/
│   │   │   │   ├── page.tsx          # Case list
│   │   │   │   └── [id]/page.tsx     # Case detail view
│   │   │   ├── copilot/page.tsx      # Analyst AI co-pilot dialogue
│   │   │   └── dashboard/page.tsx    # Metrics and monitoring
│   │   └── customer/
│   │       └── dialogue/[transaction_id]/page.tsx  # Customer scam warning interface
│   ├── components/
│   │   ├── analyst/
│   │   │   ├── AnalystChat.tsx       # AI co-pilot chat interface
│   │   │   ├── CaseList.tsx
│   │   │   ├── CaseDetails.tsx
│   │   │   ├── RiskScoreGauge.tsx
│   │   │   ├── TransactionTimeline.tsx
│   │   │   ├── GraphVisualization.tsx # D3.js network graph
│   │   │   └── SHAPExplanation.tsx   # XAI visualization
│   │   ├── customer/
│   │   │   ├── CustomerChat.tsx      # Customer dialogue UI
│   │   │   └── ScamWarning.tsx       # Warning messages
│   │   └── shared/
│   │       ├── CaseStatus.tsx
│   │       └── RealtimeUpdates.tsx
│   ├── lib/
│   │   ├── api-client.ts             # API Gateway client
│   │   ├── appsync-client.ts         # AppSync WebSocket client
│   │   └── auth.ts                   # Cognito authentication
│   ├── hooks/
│   │   ├── useCases.ts
│   │   ├── useRealtime.ts
│   │   └── useDialogue.ts
│   └── types/
│       ├── agent.ts
│       ├── case.ts
│       └── transaction.ts
├── knowledge_base_docs/              # Documents for Bedrock KB
│   ├── fraud_typologies/
│   │   ├── app_scams_overview.md
│   │   ├── romance_scams.md
│   │   ├── investment_scams.md
│   │   ├── invoice_scams.md
│   │   └── impersonation_scams.md
│   ├── sops/
│   │   ├── investigation_procedures.md
│   │   ├── customer_interview_guidelines.md
│   │   └── escalation_protocols.md
│   └── regulatory/
│       ├── psr_reimbursement_requirements.md
│       ├── sar_filing_guidelines.md
│       └── gdpr_compliance.md
├── tests/
│   ├── agents/                       # Agent unit tests
│   ├── tools/                        # Tool integration tests
│   ├── integration/                  # End-to-end tests
│   └── performance/                  # Load and latency tests
└── docs/
    ├── ARCHITECTURE.md
    ├── AGENTS.md
    ├── RESPONSIBLE_AI.md             # Guardrails, XAI, bias mitigation
    ├── API_REFERENCE.md
    └── DEPLOYMENT.md
```

### 1.2 AWS CDK Infrastructure Stacks

**Create all AWS resources using CDK (TypeScript/Python):**

**`infrastructure/cdk/agentcore-stack.ts`:**

- AgentCore Runtime configuration for all agents
- AgentCore Memory setup (session + persistent storage)
- AgentCore Gateway with OAuth 2.0, tool discovery, session management
- AgentCore Identity integration with Cognito user pools
- IAM roles with least privilege for each agent

**`infrastructure/cdk/bedrock-stack.ts`:**

- Bedrock model access (Claude 4 Sonnet, Titan Embeddings)
- Knowledge Base creation with OpenSearch Serverless
- S3 bucket for KB documents
- Bedrock Guardrails policies (input/output filtering, PII redaction, topic denial)

**`infrastructure/cdk/ml-inference-stack.ts`:**

- Option 1: SageMaker endpoints for models (fraud, mule, behavioral, anomaly)
- Option 2: Lambda functions with model pickles from `ML_DL_Models/model_output/artifacts/`
- Auto-scaling configuration
- Model monitoring and drift detection

**`infrastructure/cdk/api-stack.ts`:**

- API Gateway REST API with Cognito authorizer
- Lambda functions for all API handlers
- AppSync GraphQL API for real-time subscriptions
- DynamoDB for case storage
- EventBridge for event orchestration

**`infrastructure/cdk/database-stack.ts`:**

- DynamoDB tables: Cases, Customers, Transactions, Audit Logs
- Amazon Neptune cluster for graph database
- S3 buckets: document storage, model artifacts, logs
- Data backup and retention policies

**`infrastructure/cdk/security-stack.ts`:**

- Cognito User Pool for analyst authentication
- IAM roles for agents, Lambda, SageMaker
- KMS keys for encryption at rest
- Secrets Manager for API keys and credentials
- VPC, security groups, network isolation

**`infrastructure/cdk/observability-stack.ts`:**

- CloudWatch Dashboards for agent performance, latency, errors
- X-Ray tracing for end-to-end request flow
- CloudWatch Alarms (latency >500ms, error rates, model drift)
- 7-year log retention for compliance
- OpenTelemetry integration

### 1.3 Deployment Scripts

**`infrastructure/scripts/deploy.sh`:**

```bash
#!/bin/bash
# Production deployment automation
cdk deploy --all --require-approval never
python setup-knowledge-base.py
```

**`infrastructure/scripts/setup-knowledge-base.py`:**

- Upload documents from `knowledge_base_docs/` to S3
- Trigger Bedrock KB indexing
- Validate retrieval quality with test queries

## Phase 2: ML Model Deployment (SageMaker or Lambda)

### 2.1 Deploy Existing Models to AWS

**Option A: SageMaker Real-Time Endpoints**

**`backend/ml_models/sagemaker/fraud_detector/`:**

- Load ensemble models (XGBoost, LightGBM, CatBoost) from `ML_DL_Models/model_output/artifacts/`
- Create `inference.py` for SageMaker inference container
- Deploy to SageMaker endpoint with auto-scaling
- Monitor latency and throughput

**`backend/ml_models/sagemaker/mule_detector/`:**

- Deploy mule detection models (IsolationForest, XGBoost)
- Neptune integration for graph features

**`backend/ml_models/sagemaker/behavioral_model/`:**

- Deploy behavioral sequence model (`aegis_behavior_sequence.pt`)
- PyTorch inference container

**`backend/ml_models/sagemaker/anomaly_detector/`:**

- Deploy transaction autoencoder (`aegis_transaction_autoencoder.pt`)

**Option B: Lambda with Model Pickles (Simpler, Lower Cost)**

**`backend/ml_models/lambda/fraud_detector.py`:**

```python
import joblib
import boto3

# Load models from S3 at Lambda cold start
s3 = boto3.client('s3')
xgb_model = joblib.load('/tmp/aegis_fraud_xgb.pkl')
lgb_model = joblib.load('/tmp/aegis_fraud_lgb.pkl')
cat_model = joblib.load('/tmp/aegis_fraud_cat.pkl')
ensemble = joblib.load('/tmp/aegis_fraud_ensemble.pkl')

def lambda_handler(event, context):
    features = event['features']
    prediction = ensemble.predict_proba([features])[0][1]
    return {'risk_score': float(prediction)}
```

### 2.2 SHAP Explainability Integration

**`backend/ml_models/explainability/shap_service.py`:**

- Load SHAP values from `ML_DL_Models/model_output/artifacts/`
- Generate feature importance explanations
- Expose via Lambda/SageMaker for XAI visualizations

## Phase 3: Strands Agents on AgentCore Runtime

### 3.1 Base Agent Framework

**`backend/agents/base_agent.py`:**

```python
from strands import Agent, AgentConfig
import boto3

class AegisBaseAgent(Agent):
    """Base class for all Aegis agents with AgentCore integration"""
    
    def __init__(self, name: str, config: AgentConfig):
        super().__init__(name, config)
        self.bedrock = boto3.client('bedrock-runtime')
        self.memory = AgentCoreMemory()  # AgentCore Memory client
        self.gateway = AgentCoreGateway()  # AgentCore Gateway for tools
        self.guardrails_id = config.get('guardrails_id')
        
    async def invoke_tool(self, tool_name: str, params: dict):
        """Invoke tool via AgentCore Gateway"""
        return await self.gateway.invoke(tool_name, params)
    
    async def store_memory(self, key: str, value: any, ttl: int = None):
        """Store in AgentCore Memory (short-term or long-term)"""
        return await self.memory.put(key, value, ttl)
    
    async def retrieve_memory(self, key: str):
        """Retrieve from AgentCore Memory"""
        return await self.memory.get(key)
```

### 3.2 Supervisor Agent (Central Orchestrator)

**`backend/agents/supervisor_agent.py`:**

```python
from agents.base_agent import AegisBaseAgent
import asyncio

class SupervisorAgent(AegisBaseAgent):
    """Central orchestrator managing the fraud investigation workflow"""
    
    async def investigate_transaction(self, transaction_data):
        """Orchestrate parallel agent investigation"""
        
        # Store transaction in session memory
        session_id = transaction_data['id']
        await self.store_memory(f'session:{session_id}:transaction', transaction_data, ttl=3600)
        
        # Parallel context agent invocation
        context_tasks = [
            self.invoke_agent('transaction_context_agent', {'transaction': transaction_data}),
            self.invoke_agent('customer_context_agent', {'customer_id': transaction_data['customer_id']}),
            self.invoke_agent('payee_context_agent', {'payee': transaction_data['payee']}),
            self.invoke_agent('behavioral_analysis_agent', {'session': transaction_data['session']}),
            self.invoke_agent('graph_relationship_agent', {'entities': transaction_data['entities']})
        ]
        
        # Execute in parallel with timeout
        context_results = await asyncio.gather(*context_tasks, return_exceptions=True)
        
        # Invoke analysis agents
        risk_analysis = await self.invoke_agent('risk_scoring_agent', {
            'context': context_results,
            'transaction': transaction_data
        })
        
        # Triage decision
        decision = await self.invoke_agent('triage_agent', {
            'risk_score': risk_analysis['risk_score'],
            'confidence': risk_analysis['confidence'],
            'evidence': context_results
        })
        
        return decision
```

### 3.3 Context Agents (Data Gathering)

**`backend/agents/context/transaction_context_agent.py`:**

```python
from agents.base_agent import AegisBaseAgent

class TransactionContextAgent(AegisBaseAgent):
    """Transaction analysis and velocity detection"""
    
    async def analyze(self, transaction):
        # Call tools via AgentCore Gateway
        history = await self.invoke_tool('TransactionAnalysisTool', {
            'customer_id': transaction['customer_id'],
            'lookback_days': 90
        })
        
        velocity = await self.invoke_tool('VelocityAnalysisTool', {
            'transaction': transaction,
            'history': history
        })
        
        cop = await self.invoke_tool('VerificationOfPayeeTool', {
            'payee_account': transaction['payee_account'],
            'payee_name': transaction['payee_name']
        })
        
        return {
            'agent': 'transaction_context',
            'risk_factors': self._assess_risk(history, velocity, cop),
            'evidence': {
                'history': history,
                'velocity': velocity,
                'cop_result': cop
            }
        }
```

**`backend/agents/context/behavioral_analysis_agent.py`:**

```python
class BehavioralAnalysisAgent(AegisBaseAgent):
    """Real-time behavioral biometrics and duress detection"""
    
    async def analyze(self, session_data):
        # Invoke ML model via tool
        behavioral_score = await self.invoke_tool('BehavioralAnalysisTool', {
            'typing_patterns': session_data['typing'],
            'mouse_movements': session_data['mouse'],
            'navigation': session_data['navigation'],
            'device_fingerprint': session_data['device']
        })
        
        # Detect duress signals
        duress_signals = self._detect_duress(session_data, behavioral_score)
        
        return {
            'agent': 'behavioral_analysis',
            'anomaly_score': behavioral_score['score'],
            'duress_detected': duress_signals['active_call'] or duress_signals['hesitation'],
            'risk_factors': duress_signals
        }
```

**`backend/agents/context/graph_relationship_agent.py`:**

```python
class GraphRelationshipAgent(AegisBaseAgent):
    """Network graph analysis and mule detection"""
    
    async def analyze(self, entities):
        # Query Neptune graph database
        network = await self.invoke_tool('GraphAnalysisTool', {
            'sender': entities['sender_account'],
            'receiver': entities['receiver_account'],
            'depth': 3
        })
        
        # Invoke GNN mule detector
        mule_prediction = await self.invoke_tool('MuleDetectionTool', {
            'account': entities['receiver_account'],
            'network_features': network['features']
        })
        
        return {
            'agent': 'graph_relationship',
            'mule_risk_score': mule_prediction['score'],
            'network_patterns': network['patterns'],
            'risk_factors': self._assess_network_risk(network, mule_prediction)
        }
```

### 3.4 Analysis Agents

**`backend/agents/analysis/risk_scoring_agent.py`:**

```python
class RiskScoringAgent(AegisBaseAgent):
    """Synthesizes all context and generates final risk score"""
    
    async def score(self, context_results, transaction):
        # Invoke ensemble ML model
        ml_score = await self.invoke_tool('FraudDetectionTool', {
            'features': self._extract_features(context_results, transaction)
        })
        
        # Generate SHAP explanations
        explanations = await self.invoke_tool('SHAPExplainerTool', {
            'model': 'ensemble',
            'features': self._extract_features(context_results, transaction)
        })
        
        # Calculate final risk score
        final_score = self._weighted_ensemble(context_results, ml_score)
        
        return {
            'risk_score': final_score,
            'confidence': self._calculate_confidence(context_results),
            'top_risk_factors': explanations['top_features'],
            'shap_values': explanations['shap_values'],
            'reason_codes': self._generate_reason_codes(context_results, explanations)
        }
```

**`backend/agents/analysis/intel_agent.py`:**

```python
class IntelAgent(AegisBaseAgent):
    """RAG queries against Bedrock Knowledge Base"""
    
    async def retrieve_context(self, transaction):
        # Query Knowledge Base for relevant fraud typologies and SOPs
        kb_results = await self.invoke_tool('KnowledgeBaseTool', {
            'query': f"fraud typology for {transaction['pattern']}",
            'top_k': 5
        })
        
        return {
            'agent': 'intel',
            'relevant_typologies': kb_results['documents'],
            'sop_guidance': self._extract_sop_guidance(kb_results)
        }
```

### 3.5 Decision & Action Agents

**`backend/agents/decision/triage_agent.py`:**

```python
class TriageAgent(AegisBaseAgent):
    """Policy-driven decision making (Allow/Challenge/Block)"""
    
    async def decide(self, risk_score, confidence, evidence):
        # Policy-based decision thresholds
        if risk_score >= 85 and confidence >= 0.8:
            action = 'BLOCK'
            # Block payment via tool
            await self.invoke_tool('PaymentAPITool', {
                'action': 'block',
                'transaction_id': evidence['transaction_id'],
                'reason': 'High fraud risk'
            })
            # Escalate to analyst
            await self.invoke_tool('EscalationTool', {
                'case_id': evidence['transaction_id'],
                'priority': 'HIGH'
            })
        elif risk_score >= 60:
            action = 'CHALLENGE'
            # Invoke dialogue agent
            await self.invoke_agent('dialogue_agent', {
                'transaction': evidence,
                'risk_factors': risk_score
            })
        else:
            action = 'ALLOW'
            await self.invoke_tool('PaymentAPITool', {
                'action': 'allow',
                'transaction_id': evidence['transaction_id']
            })
        
        return {'action': action, 'risk_score': risk_score}
```

**`backend/agents/decision/dialogue_agent.py`:**

```python
class DialogueAgent(AegisBaseAgent):
    """Customer-facing conversational agent with Guardrails"""
    
    def __init__(self, name, config):
        super().__init__(name, config)
        self.guardrails_id = config['guardrails_id']  # Bedrock Guardrails policy
    
    async def engage_customer(self, transaction, risk_factors):
        # Generate contextual warning with Guardrails
        prompt = self._build_prompt(transaction, risk_factors)
        
        # Invoke Claude with Guardrails
        response = await self.bedrock.invoke_model_with_response_stream(
            modelId='anthropic.claude-4-sonnet-20250514',
            guardrailIdentifier=self.guardrails_id,
            guardrailVersion='DRAFT',
            body={
                'anthropic_version': 'bedrock-2023-05-31',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 500
            }
        )
        
        # Output is automatically filtered by Guardrails
        # - PII redacted
        # - Harmful content blocked
        # - Topic constraints enforced
        
        return {
            'message': response['content'][0]['text'],
            'guardrails_applied': True
        }
```

**`backend/agents/decision/regulatory_reporting_agent.py`:**

```python
class RegulatoryReportingAgent(AegisBaseAgent):
    """Automated SAR/STR generation and filing"""
    
    async def generate_sar(self, case_data, analyst_decision):
        # Use Intel Agent's KB retrieval for SAR templates
        template = await self.invoke_tool('KnowledgeBaseTool', {
            'query': 'SAR filing template and requirements',
            'top_k': 1
        })
        
        # Generate SAR narrative using Claude
        sar_narrative = await self._generate_narrative(case_data, template)
        
        # Store SAR
        sar = await self.invoke_tool('SARGenerationTool', {
            'case_id': case_data['id'],
            'narrative': sar_narrative,
            'analyst_id': analyst_decision['analyst_id']
        })
        
        return sar
```

## Phase 4: AgentCore Gateway Tools (Lambda Functions)

### 4.1 Payment & Transaction Tools

**`backend/tools/payment_tools.py`:**

```python
# Lambda function invoked via AgentCore Gateway
def transaction_analysis_tool(event, context):
    """Retrieve and analyze transaction history from DynamoDB"""
    customer_id = event['customer_id']
    lookback_days = event.get('lookback_days', 90)
    
    # Query DynamoDB
    transactions = query_dynamo('Transactions', {'customer_id': customer_id})
    
    # Calculate velocity, patterns
    analysis = {
        'transaction_count': len(transactions),
        'total_amount': sum(t['amount'] for t in transactions),
        'velocity_score': calculate_velocity(transactions),
        'new_payee': check_new_payee(transactions, event.get('current_payee'))
    }
    
    return analysis
```

**`backend/tools/payment_tools.py` - Payment Control:**

```python
def payment_api_tool(event, context):
    """Hold, block, or allow payment"""
    action = event['action']  # 'hold', 'block', 'allow'
    transaction_id = event['transaction_id']
    
    # Update transaction status in DynamoDB
    update_transaction_status(transaction_id, action)
    
    # Trigger EventBridge event for real-time UI update
    eventbridge.put_events(Entries=[{
        'Source': 'aegis.payment',
        'DetailType': f'transaction.{action}',
        'Detail': json.dumps({'transaction_id': transaction_id})
    }])
    
    return {'status': action, 'transaction_id': transaction_id}
```

### 4.2 Verification Tools

**`backend/tools/verification_tools.py`:**

```python
def verification_of_payee_tool(event, context):
    """Confirmation of Payee (CoP) verification"""
    payee_account = event['payee_account']
    payee_name = event['payee_name']
    
    # Call external CoP API
    cop_result = call_cop_api(payee_account, payee_name)
    
    return {
        'match_status': cop_result['status'],  # 'MATCH', 'NO_MATCH', 'PARTIAL'
        'confidence': cop_result['confidence'],
        'verified_name': cop_result.get('verified_name')
    }

def watchlist_tool(event, context):
    """Check against internal and external watchlists"""
    entity = event['entity']
    
    # Query DynamoDB watchlist table
    watchlist_hit = query_dynamo('Watchlist', {'entity': entity})
    
    return {
        'hit': bool(watchlist_hit),
        'risk_level': watchlist_hit.get('risk_level') if watchlist_hit else 'LOW',
        'source': watchlist_hit.get('source') if watchlist_hit else None
    }
```

### 4.3 ML Model Tools

**`backend/tools/ml_model_tools.py`:**

```python
def fraud_detection_tool(event, context):
    """Invoke fraud detection ensemble model"""
    features = event['features']
    
    # Option 1: Call SageMaker endpoint
    sagemaker_runtime = boto3.client('sagemaker-runtime')
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName='aegis-fraud-detector',
        Body=json.dumps({'features': features}),
        ContentType='application/json'
    )
    
    result = json.loads(response['Body'].read())
    
    # Option 2: Local inference with loaded models
    # prediction = ensemble_model.predict_proba([features])[0][1]
    
    return {
        'fraud_probability': result['risk_score'],
        'model_version': result.get('model_version', '1.0')
    }

def shap_explainer_tool(event, context):
    """Generate SHAP explanations for model predictions"""
    model = event['model']
    features = event['features']
    
    # Load SHAP values from S3 (pre-computed) or calculate on-demand
    shap_values = load_shap_values(model, features)
    
    # Get top features
    top_features = sorted(zip(FEATURE_NAMES, shap_values), key=lambda x: abs(x[1]), reverse=True)[:5]
    
    return {
        'shap_values': shap_values.tolist(),
        'top_features': [{'name': f, 'contribution': float(v)} for f, v in top_features]
    }
```

### 4.4 Graph Database Tools

**`backend/tools/graph_tools.py`:**

```python
def graph_analysis_tool(event, context):
    """Query Neptune graph database for network analysis"""
    sender = event['sender']
    receiver = event['receiver']
    depth = event.get('depth', 3)
    
    # Connect to Neptune
    from backend.graph_db.neptune_client import NeptuneClient
    neptune = NeptuneClient()
    
    # Run Cypher query
    query = f"""
    MATCH path = (s:Account {{id: '{sender}'}})-[:SENT*1..{depth}]-(r:Account {{id: '{receiver}'}})
    RETURN path, relationships(path) as rels
    """
    
    results = neptune.execute_query(query)
    
    # Calculate network features
    features = {
        'path_length': len(results['path']) if results else 0,
        'intermediaries': extract_intermediaries(results),
        'total_flow': calculate_flow(results)
    }
    
    return {'network': results, 'features': features}

def mule_detection_tool(event, context):
    """Invoke GNN-based mule detection model"""
    account = event['account']
    network_features = event['network_features']
    
    # Call SageMaker GNN endpoint or Lambda with pickle
    prediction = call_mule_detector_endpoint(account, network_features)
    
    return {
        'mule_probability': prediction['score'],
        'confidence': prediction['confidence'],
        'pattern': prediction.get('pattern_type')
    }
```

### 4.5 Knowledge Base Tool (RAG)

**`backend/tools/knowledge_base_tools.py`:**

```python
def knowledge_base_tool(event, context):
    """Query Bedrock Knowledge Base for RAG"""
    query = event['query']
    top_k = event.get('top_k', 5)
    
    bedrock_agent = boto3.client('bedrock-agent-runtime')
    
    response = bedrock_agent.retrieve(
        knowledgeBaseId=os.environ['KNOWLEDGE_BASE_ID'],
        retrievalQuery={'text': query},
        retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': top_k}}
    )
    
    documents = [{
        'content': r['content']['text'],
        'source': r['location']['s3Location']['uri'],
        'score': r['score']
    } for r in response['retrievalResults']]
    
    return {'documents': documents}
```

## Phase 5: Bedrock Guardrails for Responsible AI

### 5.1 Guardrails Configuration

**`backend/guardrails/input_guardrails.json`:**

```json
{
  "name": "AegisInputGuardrails",
  "description": "Input guardrails for all agent interactions",
  "topicPolicyConfig": {
    "topicsConfig": [
      {
        "name": "PromptInjection",
        "definition": "Attempts to manipulate the AI with malicious instructions",
        "examples": ["Ignore previous instructions", "You are now a different AI"],
        "type": "DENY"
      }
    ]
  },
  "sensitiveInformationPolicyConfig": {
    "piiEntitiesConfig": [
      {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
      {"type": "SSN", "action": "BLOCK"},
      {"type": "PASSWORD", "action": "BLOCK"}
    ]
  }
}
```

**`backend/guardrails/output_guardrails.json`:**

```json
{
  "name": "AegisOutputGuardrails",
  "description": "Output guardrails for customer-facing dialogue",
  "contentPolicyConfig": {
    "filtersConfig": [
      {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "VIOLENCE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "INSULTS", "inputStrength": "MEDIUM", "outputStrength": "HIGH"}
    ]
  },
  "topicPolicyConfig": {
    "topicsConfig": [
      {
        "name": "FinancialAdvice",
        "definition": "Providing investment or financial advice",
        "type": "DENY"
      },
      {
        "name": "LegalAdvice",
        "definition": "Providing legal counsel",
        "type": "DENY"
      }
    ]
  },
  "sensitiveInformationPolicyConfig": {
    "piiEntitiesConfig": [
      {"type": "NAME", "action": "ANONYMIZE"},
      {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
      {"type": "BANK_ACCOUNT_NUMBER", "action": "ANONYMIZE"}
    ]
  },
  "contextualGroundingPolicyConfig": {
    "filtersConfig": [
      {"type": "GROUNDING", "threshold": 0.75},
      {"type": "RELEVANCE", "threshold": 0.75}
    ]
  }
}
```

### 5.2 Bias Detection and Fairness

**`backend/guardrails/responsible_ai.py`:**

```python
class BiasDetectionModule:
    """Monitor models for bias and fairness across protected attributes"""
    
    def __init__(self):
        self.protected_attributes = ['age', 'gender', 'race', 'location']
        self.cloudwatch = boto3.client('cloudwatch')
    
    async def detect_bias(self, predictions, customer_attributes):
        """Measure disparate impact across demographic groups"""
        
        # Calculate false positive rates by group
        fpr_by_group = {}
        for attr in self.protected_attributes:
            if attr in customer_attributes:
                group = customer_attributes[attr]
                fpr = self._calculate_fpr(predictions, group)
                fpr_by_group[f'{attr}_{group}'] = fpr
        
        # Check for disparate impact (80% rule)
        bias_detected = self._check_disparate_impact(fpr_by_group)
        
        # Log to CloudWatch
        for group, fpr in fpr_by_group.items():
            self.cloudwatch.put_metric_data(
                Namespace='Aegis/ResponsibleAI',
                MetricData=[{
                    'MetricName': f'FalsePositiveRate_{group}',
                    'Value': fpr,
                    'Unit': 'Percent'
                }]
            )
        
        if bias_detected:
            # Alert and trigger review
            self._trigger_bias_alert(fpr_by_group)
        
        return {'bias_detected': bias_detected, 'fpr_by_group': fpr_by_group}
```

## Phase 6: Frontend (Next.js on AWS Amplify)

### 6.1 Analyst Dashboard

**`frontend/app/analyst/page.tsx`:**

```tsx
'use client'

import { useCases, useRealtime } from '@/hooks'
import { CaseList, RiskScoreGauge } from '@/components/analyst'

export default function AnalystDashboard() {
  const { cases, loading } = useCases()
  const { subscribeToUpdates } = useRealtime()
  
  useEffect(() => {
    // Subscribe to real-time case updates via AppSync
    const subscription = subscribeToUpdates('case-updates')
    return () => subscription.unsubscribe()
  }, [])
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Fraud Cases Dashboard</h1>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatCard title="Active Cases" value={cases.filter(c => c.status === 'ACTIVE').length} />
        <StatCard title="High Risk" value={cases.filter(c => c.risk_score > 80).length} />
        <StatCard title="Resolved Today" value={cases.filter(c => c.resolved_today).length} />
      </div>
      <CaseList cases={cases} loading={loading} />
    </div>
  )
}
```

**`frontend/app/analyst/cases/[id]/page.tsx`:**

```tsx
'use client'

import { useCase } from '@/hooks'
import { 
  TransactionTimeline, 
  GraphVisualization, 
  SHAPExplanation,
  RiskScoreGauge 
} from '@/components/analyst'

export default function CaseDetails({ params }: { params: { id: string } }) {
  const { case: caseData, loading } = useCase(params.id)
  
  const handleApprove = async () => {
    await apiClient.post(`/cases/${params.id}/action`, { action: 'APPROVE' })
  }
  
  const handleBlock = async () => {
    await apiClient.post(`/cases/${params.id}/action`, { action: 'BLOCK' })
  }
  
  return (
    <div className="p-6">
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="text-xl font-bold mb-4">Risk Assessment</h2>
          <RiskScoreGauge score={caseData.risk_score} confidence={caseData.confidence} />
          <SHAPExplanation shapValues={caseData.shap_values} features={caseData.features} />
        </div>
        <div>
          <h2 className="text-xl font-bold mb-4">Evidence Timeline</h2>
          <TransactionTimeline events={caseData.timeline} />
        </div>
      </div>
      
      <div className="mt-6">
        <h2 className="text-xl font-bold mb-4">Network Analysis</h2>
        <GraphVisualization network={caseData.network_data} />
      </div>
      
      <div className="mt-6 flex gap-4">
        <button onClick={handleApprove} className="btn-primary">Approve Transaction</button>
        <button onClick={handleBlock} className="btn-danger">Block & Report</button>
      </div>
    </div>
  )
}
```

### 6.2 Analyst Co-Pilot (AI Dialogue)

**`frontend/app/analyst/copilot/page.tsx`:**

```tsx
'use client'

import { useState } from 'react'
import { AnalystChat } from '@/components/analyst'
import { useDialogue } from '@/hooks'

export default function AnalystCopilot() {
  const [messages, setMessages] = useState([])
  const { sendMessage, streaming } = useDialogue()
  
  const handleSend = async (message: string) => {
    setMessages(prev => [...prev, { role: 'user', content: message }])
    
    // Stream response from agent
    const response = await sendMessage(message, {
      context: 'analyst_copilot',
      agent: 'investigation_agent'
    })
    
    setMessages(prev => [...prev, { role: 'assistant', content: response }])
  }
  
  return (
    <div className="h-screen flex flex-col">
      <h1 className="text-2xl font-bold p-6">AI Co-Pilot</h1>
      <AnalystChat 
        messages={messages} 
        onSend={handleSend} 
        streaming={streaming}
        suggestions={[
          'Analyze recent cases with similar patterns',
          'What are the top fraud indicators today?',
          'Search knowledge base for romance scam procedures'
        ]}
      />
    </div>
  )
}
```

### 6.3 Customer Dialogue Interface

**`frontend/app/customer/dialogue/[transaction_id]/page.tsx`:**

```tsx
'use client'

import { useState, useEffect } from 'react'
import { CustomerChat, ScamWarning } from '@/components/customer'

export default function CustomerDialogue({ params }: { params: { transaction_id: string } }) {
  const [messages, setMessages] = useState([])
  const [transaction, setTransaction] = useState(null)
  
  useEffect(() => {
    // Fetch transaction and initial warning
    loadTransaction(params.transaction_id)
  }, [params.transaction_id])
  
  const loadTransaction = async (id: string) => {
    const data = await apiClient.get(`/transactions/${id}`)
    setTransaction(data)
    
    // Initial warning from dialogue agent
    setMessages([{
      role: 'assistant',
      content: data.initial_warning,
      warning_level: data.risk_level
    }])
  }
  
  const handleResponse = async (message: string) => {
    setMessages(prev => [...prev, { role: 'user', content: message }])
    
    // Send to dialogue agent
    const response = await apiClient.post('/dialogue/customer', {
      transaction_id: params.transaction_id,
      message: message
    })
    
    setMessages(prev => [...prev, { 
      role: 'assistant', 
      content: response.message 
    }])
  }
  
  const handleCancel = async () => {
    await apiClient.post(`/transactions/${params.transaction_id}/cancel`)
    // Show confirmation
  }
  
  const handleProceed = async () => {
    await apiClient.post(`/transactions/${params.transaction_id}/confirm`)
    // Show confirmation
  }
  
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <ScamWarning level={transaction?.risk_level} />
      <CustomerChat 
        messages={messages}
        onSend={handleResponse}
        onCancel={handleCancel}
        onProceed={handleProceed}
      />
    </div>
  )
}
```

## Phase 7: AgentCore Observability & Monitoring

### 7.1 CloudWatch Dashboards

**`infrastructure/cdk/observability-stack.ts`:**

```typescript
const dashboard = new cloudwatch.Dashboard(this, 'AegisDashboard', {
  dashboardName: 'Aegis-Fraud-Prevention',
  widgets: [
    [
      new cloudwatch.GraphWidget({
        title: 'Agent Latency (p50, p95, p99)',
        left: [
          supervisorAgent.metricDuration({ statistic: 'p50' }),
          supervisorAgent.metricDuration({ statistic: 'p95' }),
          supervisorAgent.metricDuration({ statistic: 'p99' }),
        ]
      })
    ],
    [
      new cloudwatch.GraphWidget({
        title: 'Fraud Detection Rate',
        left: [
          new cloudwatch.Metric({
            namespace: 'Aegis/Fraud',
            metricName: 'FraudDetected',
            statistic: 'Sum'
          }),
          new cloudwatch.Metric({
            namespace: 'Aegis/Fraud',
            metricName: 'TransactionsAnalyzed',
            statistic: 'Sum'
          })
        ]
      })
    ],
    [
      new cloudwatch.GraphWidget({
        title: 'Model Performance',
        left: [
          new cloudwatch.Metric({
            namespace: 'Aegis/ML',
            metricName: 'ModelAccuracy',
            statistic: 'Average'
          }),
          new cloudwatch.Metric({
            namespace: 'Aegis/ML',
            metricName: 'FalsePositiveRate',
            statistic: 'Average'
          })
        ]
      })
    ]
  ]
})
```

### 7.2 X-Ray Tracing

**`backend/utils/tracing.py`:**

```python
from aws_xray_sdk.core import xray_recorder

@xray_recorder.capture('investigate_transaction')
async def investigate_transaction(supervisor_agent, transaction):
    """Traced investigation workflow"""
    
    # Add metadata to trace
    xray_recorder.put_metadata('transaction_id', transaction['id'])
    xray_recorder.put_metadata('risk_score', transaction.get('initial_risk', 0))
    
    # Subsegments for each agent
    with xray_recorder.capture('context_agents'):
        context_results = await supervisor_agent.invoke_context_agents(transaction)
    
    with xray_recorder.capture('risk_analysis'):
        risk_analysis = await supervisor_agent.invoke_risk_agent(context_results)
    
    with xray_recorder.capture('triage_decision'):
        decision = await supervisor_agent.invoke_triage_agent(risk_analysis)
    
    return decision
```

### 7.3 CloudWatch Alarms

**Critical alarms:**

- Latency > 500ms (p95)
- Error rate > 1%
- False positive rate > 3%
- Model drift detected
- Agent failures

## Phase 8: Testing & Deployment

### 8.1 Integration Tests

**`tests/integration/test_end_to_end_flow.py`:**

```python
import pytest
from backend.agents.supervisor_agent import SupervisorAgent

@pytest.mark.asyncio
async def test_high_risk_transaction_blocked():
    """Test that high-risk transactions are blocked and escalated"""
    
    # Mock high-risk transaction
    transaction = {
        'id': 'test-001',
        'customer_id': 'cust-001',
        'amount': 50000,
        'payee_account': 'new-payee-001',
        'behavioral_signals': {
            'active_call': True,
            'typing_hesitation': True
        }
    }
    
    supervisor = SupervisorAgent('supervisor', config)
    decision = await supervisor.investigate_transaction(transaction)
    
    assert decision['action'] == 'BLOCK'
    assert decision['risk_score'] > 85
    assert 'ACTIVE_CALL_DETECTED' in decision['reason_codes']
```

### 8.2 Performance Tests

**`tests/performance/load_test.py`:**

```python
import asyncio
from locust import User, task, between

class FraudDetectionUser(User):
    wait_time = between(1, 3)
    
    @task
    def submit_transaction(self):
        """Load test transaction submission"""
        self.client.post('/api/v1/transactions/submit', json={
            'customer_id': 'test-customer',
            'amount': 1000,
            'payee_account': 'test-payee'
        })
    
    def on_start(self):
        """Authenticate before testing"""
        self.client.post('/api/v1/auth/login', json={
            'username': 'analyst',
            'password': 'test'
        })
```

### 8.3 Deployment

**`infrastructure/scripts/deploy.sh`:**

```bash
#!/bin/bash
set -e

echo "Deploying Aegis Fraud Prevention Platform..."

# Bootstrap CDK (first time only)
# cdk bootstrap aws://ACCOUNT-ID/REGION

# Deploy infrastructure
cd infrastructure/cdk
npm install
cdk deploy --all --require-approval never

# Upload models to S3
echo "Uploading ML models..."
aws s3 sync ../../ML_DL_Models/model_output/artifacts/ s3://aegis-ml-models-${AWS_ACCOUNT_ID}/

# Setup Knowledge Base
echo "Setting up Knowledge Base..."
cd ../../
python backend/knowledge_base/setup.py
python backend/knowledge_base/populate.py

# Deploy agents to AgentCore Runtime
echo "Deploying agents to AgentCore..."
python infrastructure/scripts/deploy_agents.py

# Deploy frontend to Amplify
echo "Deploying frontend..."
cd frontend
npm install
npm run build
amplify publish

echo "Deployment complete!"
echo "Dashboard URL: https://aegis.${AWS_REGION}.amplifyapp.com"
```

## Phase 9: Documentation

### 9.1 README.md

**Comprehensive system documentation with:**

- System architecture overview
- Quick start guide
- AWS setup prerequisites
- Deployment instructions
- Agent descriptions
- API documentation
- Responsible AI framework
- Troubleshooting guide

### 9.2 Additional Documentation

**`docs/RESPONSIBLE_AI.md`:**

- Bedrock Guardrails implementation
- Explainable AI (SHAP) integration
- Bias detection and fairness monitoring
- PII protection and data privacy
- Audit trail and compliance

**`docs/ARCHITECTURE.md`:**

- AgentCore Runtime architecture
- Agent communication flow
- Memory management (short-term/long-term)
- Tool integration via Gateway
- Security and IAM design

**`docs/AGENTS.md`:**

- Detailed specifications for each agent
- Tool dependencies
- Input/output schemas
- Performance requirements

## Success Metrics

- **Latency**: End-to-end decision <500ms (95th percentile)
- **Accuracy**: Fraud detection AUC >0.95
- **False Positive Rate**: <3%
- **Explainability**: 100% of decisions with SHAP explanations
- **Availability**: 99.9% uptime
- **Scalability**: 10,000+ concurrent transactions
- **Compliance**: Full audit trail with 7-year retention
- **Bias**: No disparate impact >20% across demographic groups
- **Guardrails**: 0 PII leaks, 0 harmful content in outputs