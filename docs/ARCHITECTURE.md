# Aegis System Architecture

## Overview

Aegis is a production-ready, multi-agent AI fraud prevention platform built entirely on AWS Bedrock AgentCore with comprehensive Responsible AI principles.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AWS Bedrock AgentCore Runtime                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐      ┌─────────────────────────────────────┐     │
│  │  Supervisor  │─────▶│  Context Agents (Parallel)          │     │
│  │    Agent     │      │  • Transaction Context               │     │
│  └──────────────┘      │  • Customer Context                  │     │
│         │              │  • Payee Context                     │     │
│         │              │  • Behavioral Analysis               │     │
│         │              │  • Graph Relationship                │     │
│         ▼              └─────────────────────────────────────┘     │
│  ┌──────────────┐      ┌─────────────────────────────────────┐     │
│  │   Analysis   │─────▶│  Decision & Action Agents           │     │
│  │    Agents    │      │  • Triage Agent                     │     │
│  │ • Risk Score │      │  • Dialogue Agent (Guardrails)      │     │
│  │ • Intel/RAG  │      │  • Investigation Agent              │     │
│  └──────────────┘      │  • Policy Decision Agent            │     │
│                        │  • Regulatory Reporting Agent       │     │
│                        └─────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────────┤
│                     AgentCore Gateway (MCP Tools)                    │
│  Lambda Functions: ML Models • Payment API • Verification •          │
│  Graph DB • Knowledge Base • Behavioral • Case Management            │
├─────────────────────────────────────────────────────────────────────┤
│                      AgentCore Memory & Identity                     │
│  Short-term: Session Memory (3600s TTL) | Long-term: User Profiles  │
│  IAM Roles: Least Privilege | Cognito: Analyst Authentication       │
└─────────────────────────────────────────────────────────────────────┘
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Bedrock KB     │      │  Amazon Neptune  │      │  DynamoDB +      │
│  (OpenSearch)   │      │  Graph Database  │      │  S3 + SageMaker  │
│  Fraud Docs     │      │  Mule Networks   │      │  Cases + Models  │
└─────────────────┘      └──────────────────┘      └──────────────────┘
```

## Core Components

### 1. AgentCore Runtime
- **Purpose**: Serverless, managed runtime for all agents
- **Features**:
  - Session isolation (prevents data leakage)
  - Extended runtime (up to 8 hours for complex investigations)
  - Auto-scaling based on load
  - Built-in observability

### 2. AgentCore Memory
- **Short-term Memory**: DynamoDB with TTL for active investigations
- **Long-term Memory**: Persistent storage for customer profiles, case history
- **Access Pattern**: Key-value store with session-based keys
- **TTL**: Configurable (default 1 hour for sessions, permanent for profiles)

### 3. AgentCore Gateway
- **Protocol**: Model Context Protocol (MCP)
- **Tools**: Lambda functions for all external interactions
- **Authentication**: OAuth 2.0 with automatic session ID injection
- **Rate Limiting**: Configurable per tool

### 4. AgentCore Identity
- **Authentication**: AWS Cognito for analysts
- **Authorization**: IAM roles with least privilege
- **Agent Permissions**: Each agent type has specific IAM role
- **Service Access**: Agents assume roles to access AWS resources

### 5. AgentCore Observability
- **Metrics**: CloudWatch custom metrics (latency, errors, fraud rate)
- **Logs**: Structured JSON logs with 7-year retention
- **Tracing**: X-Ray distributed tracing for end-to-end visibility
- **Dashboards**: Pre-configured CloudWatch dashboards

## Agent Architecture

### Agent Hierarchy

1. **Supervisor Agent** (Orchestrator)
   - Manages investigation workflow
   - Parallel agent invocation
   - Result aggregation
   - Decision routing

2. **Context Agents** (Data Gathering)
   - Transaction Context
   - Customer Context
   - Payee Context
   - Behavioral Analysis
   - Graph Relationship

3. **Analysis Agents** (Intelligence)
   - Risk Scoring (ML + SHAP)
   - Intel (RAG from Knowledge Base)

4. **Decision Agents** (Action)
   - Triage (Policy-based decisions)
   - Dialogue (Customer-facing with Guardrails)
   - Investigation (Deep-dive analysis)
   - Policy Decision (Human-in-the-loop)
   - Regulatory Reporting (SAR/STR generation)

### Agent Communication

- **Synchronous**: Supervisor → Context/Analysis → Decision
- **Parallel**: All Context Agents execute simultaneously
- **Timeout**: 30s for context, 25s for analysis, 60s total
- **Failure Handling**: Graceful degradation with partial results

### Agent State Management

- **Stateless**: Agents don't maintain state between invocations
- **Session State**: Stored in AgentCore Memory
- **Persistent State**: Stored in DynamoDB
- **State Keys**: `session:{id}:*` for temporary, `profile:{id}:*` for persistent

## Data Flow

### Transaction Investigation Flow

1. **Ingestion** (< 10ms)
   - Transaction submitted via API
   - Initial validation
   - Supervisor Agent invoked

2. **Context Gathering** (< 75ms)
   - 5 Context Agents execute in parallel
   - Each queries different data sources
   - Results stored in session memory

3. **Analysis** (< 150ms)
   - Risk Scoring Agent invokes ML models
   - Intel Agent queries Knowledge Base
   - SHAP explanations generated
   - Final risk score calculated

4. **Decision** (< 50ms)
   - Triage Agent evaluates risk score
   - Policy-based action determined
   - Payment API called (allow/hold/block)

5. **Action** (< 200ms)
   - If CHALLENGE: Dialogue Agent engaged
   - If BLOCK: Escalation Tool creates case
   - If ALLOW: Transaction proceeds

**Total Latency Target**: < 500ms (p95)

## Data Storage

### DynamoDB Tables

1. **aegis-cases**
   - Primary Key: case_id
   - GSI: status-created-index
   - TTL: None (permanent)
   - Use: Case management

2. **aegis-transactions**
   - Primary Key: transaction_id
   - GSI: customer-timestamp-index
   - TTL: None
   - Use: Transaction history

3. **aegis-customers**
   - Primary Key: customer_id
   - TTL: None
   - Use: Customer profiles

4. **aegis-audit-logs**
   - Primary Key: log_id, timestamp
   - TTL: 7 years
   - Use: Compliance audit trail

5. **aegis-cases-memory**
   - Primary Key: memory_key
   - TTL: 1 hour (configurable)
   - Use: AgentCore Memory (sessions)

### S3 Buckets

1. **aegis-ml-models-{account}**
   - ML model artifacts (pickles, checkpoints)
   - SHAP values (pre-computed)
   - Model metadata

2. **aegis-kb-documents-{account}**
   - Knowledge Base documents
   - Fraud typologies
   - SOPs and procedures
   - Regulatory guidance

### Amazon Neptune

- **Nodes**: Accounts, Customers, Transactions
- **Relationships**: SENT, RECEIVED, OWNS, LINKED_TO
- **Queries**: Mule detection, network analysis
- **Performance**: Sub-10ms for 3-hop queries

### Bedrock Knowledge Base

- **Vector Store**: OpenSearch Serverless
- **Embeddings**: Titan Embeddings v2
- **Documents**: 100+ fraud typologies, SOPs
- **Query Latency**: < 100ms for top-5 results

## Security Architecture

### Network Security

- **VPC**: Private subnets for Neptune, Lambda
- **Security Groups**: Minimal ingress rules
- **PrivateLink**: For Bedrock access
- **WAF**: Rate limiting, IP filtering

### Data Security

- **Encryption at Rest**: KMS for all data stores
- **Encryption in Transit**: TLS 1.3
- **PII Protection**: Guardrails redact/anonymize PII
- **Access Logs**: All API calls logged

### IAM Structure

```
AgentCore Identity
├── SupervisorAgentRole
│   ├── Invoke Context Agents
│   ├── Write to AgentCore Memory
│   └── Read from DynamoDB
├── ContextAgentRole
│   ├── Invoke Tools (Gateway)
│   ├── Read from DynamoDB
│   └── Write to AgentCore Memory
├── AnalysisAgentRole
│   ├── Invoke SageMaker Endpoints
│   ├── Query Knowledge Base
│   └── Read from AgentCore Memory
└── DecisionAgentRole
    ├── Write to DynamoDB (cases)
    ├── Publish to EventBridge
    └── Invoke Bedrock with Guardrails
```

## Scalability

### Horizontal Scaling

- **AgentCore Runtime**: Auto-scales to handle load
- **Lambda Functions**: Concurrent execution (1000+ default)
- **DynamoDB**: On-demand billing, auto-scaling
- **Neptune**: Read replicas for query scaling

### Performance Optimization

- **Parallel Execution**: Context agents run simultaneously
- **Caching**: Frequent KB queries cached
- **Connection Pooling**: Reuse DynamoDB connections
- **Batch Operations**: Bulk writes to DynamoDB

### Capacity Planning

- **Target**: 10,000 concurrent transactions
- **Peak**: 50,000 TPS during business hours
- **Storage**: 100M transactions/year (500GB)
- **Retention**: 7 years (compliance)

## Disaster Recovery

### Backup Strategy

- **DynamoDB**: Point-in-time recovery enabled
- **S3**: Versioning + cross-region replication
- **Neptune**: Daily snapshots
- **Configuration**: IaC (CDK) in version control

### Recovery Objectives

- **RTO**: 1 hour (critical systems)
- **RPO**: 5 minutes (transaction data)
- **Multi-Region**: Active-passive setup

## Monitoring & Alerting

### Key Metrics

1. **Performance**
   - End-to-end latency (p50, p95, p99)
   - Agent execution time
   - Tool invocation latency

2. **Accuracy**
   - Fraud detection rate
   - False positive rate
   - Model accuracy (AUC)

3. **System Health**
   - Error rate
   - Timeout rate
   - DynamoDB throttling

4. **Business**
   - Transactions analyzed
   - Cases escalated
   - SARs filed

### Critical Alarms

- Latency > 500ms (p95)
- Error rate > 1%
- False positive rate > 3%
- Model drift detected
- DynamoDB capacity exceeded

## Future Enhancements

1. **Multi-Region Active-Active**
2. **Real-time Model Retraining**
3. **Advanced Graph Algorithms** (Community detection)
4. **Federated Learning** (Cross-bank collaboration)
5. **Quantum-Resistant Encryption**



