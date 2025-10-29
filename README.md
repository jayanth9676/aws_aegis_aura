# Aegis Agentic AI Platform

Real-time Authorized Push Payment (APP) scam prevention built on AWS Bedrock AgentCore, Strands Agents, and a production-grade multi-agent architecture.

## Highlights
- 13 collaborating Bedrock agents orchestrated by the Supervisor agent for end-to-end scam investigations (context → analysis → decision).
- 8 AgentCore Gateway Lambda tools for payments, customer data, graph intelligence, ML inference, regulatory workflows, and knowledge retrieval.
- FastAPI backend with WebSocket streaming, Next.js analyst/customer portals, and deployment scripts for Bedrock guardrails, knowledge base, and ML endpoints.
- Responsible AI baked in: guardrails, SHAP explainability, bias monitoring, audit logging, and security controls aligned to financial-services regulations.

### TECHNICAL ARCHITECTURE
![Technical Architecture](/tech_arch%20diagram.drawio.png)


Refer to `docs/ARCHITECTURE.md` and `docs/AGENTS.md` for deep technical detail.

## Repository Layout
```
authorised_push_payments/
├── backend/               # Agents, FastAPI API, tools, graph + ML integrations
├── frontend/              # Next.js 14 analyst & customer experience
├── infrastructure/        # CDK stacks & helper scripts
├── knowledge_base_docs/   # Fraud typologies, SOPs, regulatory guidance
├── datasets/              # Sample datasets for local experimentation
├── ML_DL_Models/          # Model training, inference, monitoring assets
├── docs/                  # Architecture, guardrails, deployment documentation
└── tests/                 # Python unit, integration, performance suites
```

## Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- AWS CLI v2 configured with credentials that can access Bedrock, AgentCore, DynamoDB, Neptune, SageMaker, and Cognito
- Optional: `uv` for Python dependency management (repository ships with `uv.lock`)

## Setup

### 1. Clone & Python Environment
```bash
git clone <repository-url>
cd agenticai_for_authorized_push_payments
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 2. Configure Secrets & Environment
Create a local `.env` (not committed) or use AWS Secrets Manager/Parameter Store. Minimum variables required for AgentCore and AWS integration are defined in the config modules, for example:
```55:70:backend/config/agentcore_config.py
agentcore_config = AgentCoreConfig(
    region=os.getenv("AWS_REGION", "us-east-1"),
    runtime_arn=os.getenv("AGENTCORE_RUNTIME_ARN"),
    ...
    gateway_client_id=os.getenv("GATEWAY_CLIENT_ID"),
    gateway_client_secret=os.getenv("GATEWAY_CLIENT_SECRET"),
    gateway_token_endpoint=os.getenv("GATEWAY_TOKEN_ENDPOINT"),
    gateway_scope=os.getenv("GATEWAY_SCOPE", "invoke"),
    gateway_access_token=os.getenv("GATEWAY_ACCESS_TOKEN"),
)
```
Key secrets to populate:
- `GATEWAY_CLIENT_ID`, `GATEWAY_CLIENT_SECRET`, `GATEWAY_TOKEN_ENDPOINT`, `GATEWAY_SCOPE`
- `AGENTCORE_GATEWAY_ENDPOINT`, `AGENTCORE_RUNTIME_ARN`, `AGENTCORE_EXECUTION_ROLE_ARN`
- `AWS_REGION`, `AWS_ACCOUNT_ID`
- DynamoDB/Neptune identifiers: `CASES_TABLE`, `TRANSACTIONS_TABLE`, `NEPTUNE_ENDPOINT`, etc.
- Guardrails, Knowledge Base, and model endpoints (`GUARDRAILS_ID`, `KNOWLEDGE_BASE_ID`, `FRAUD_DETECTOR_ENDPOINT`, ...)

> ⚠️ `gateway_config.json` and `backend/.bedrock_agentcore*.yaml` contain live identifiers and must stay out of source control. Keep them in secure storage and follow `security.md` notes below.

### 3. Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

## Running the Platform

### Start Backend API & WebSocket
```bash
uvicorn backend.api.main:app --reload --port 8000
```
- REST endpoints under `http://localhost:8000/api/v1/`
- Interactive docs at `http://localhost:8000/docs`
- WebSocket stream at `ws://localhost:8000/ws`

### Run Supervisor Demo (optional)
```bash
python main.py
```
Launches a scripted transaction investigation that walks through the multi-agent workflow end-to-end.

### Start Frontend Apps
```bash
cd frontend
npm run dev
```
- Analyst dashboard: `http://localhost:3000/analyst`
- Customer portal (scam dialogue): `http://localhost:3000/customer`

## Data & Knowledge Base
- `knowledge_base_docs/` ships with fraud typologies, SOPs, and regulatory references. Load them via `backend/knowledge_base/setup.py` and `populate.py`.
- Synthetic datasets for experimentation live under `datasets/` and `ML_DL_Models/`. These are optional for local demos but excluded from deployment pipelines.

## Testing & Quality
```bash
# Backend
pytest --maxfail=1 --disable-warnings -q
pytest --cov=backend --cov-report=xml

# Frontend
cd frontend
npm run test
```
Additional suites exist in `tests/performance/` for load testing and `tests/integration/` for end-to-end agent flows.

## Security & Responsible AI Checklist
- **Secrets**: Store Bedrock/AgentCore credentials in AWS Secrets Manager or local `.env`; rotate anything previously committed.
- **Guardrails**: Configure Bedrock guardrails before enabling customer-facing dialogue agents. JSON templates live in `backend/guardrails/`.
- **Explainability**: SHAP explainers stored under `backend/ml_models/explainability/` must be deployed alongside fraud models to keep audit reports complete.
- **Audit Logging**: DynamoDB audit table defaults (`aegis-audit-logs`) can be overridden via env vars in `SystemConfig`.
- **Bias Monitoring**: `backend/guardrails/responsible_ai.py` runs disparate-impact checks; wire metrics to CloudWatch before go-live.

## Deployment Workflow (Summary)
1. Deploy AWS infrastructure with the CDK stacks in `infrastructure/cdk/`.
2. Set up guardrails (`infrastructure/bedrock_guardrails/deploy_guardrails.py`).
3. Upload ML artifacts to S3 and deploy endpoints via `infrastructure/scripts/deploy_ml_models.py`.
4. Register tools with AgentCore Gateway and sync config into Secrets Manager.
5. Publish Strands agents (`infrastructure/scripts/deploy_agents.py`) and frontends (Amplify).

Detailed, step-by-step guidance is in:
- `docs/DEPLOYMENT.md`
- `docs/agentcore_runtime.md`
- `docs/RESPONSIBLE_AI.md`

## Troubleshooting
- **Gateway auth errors**: confirm `GATEWAY_CLIENT_*` values and scopes. Tokens must be retrieved via OAuth2 client credentials flow.
- **Neptune connection issues**: set `NEPTUNE_ENDPOINT` and whitelist the runtime VPC security groups.
- **High latency**: review agent timeout overrides in `AgentConfig` and ensure parallel context agents are enabled.
- **Missing datasets/models**: run the scripts under `datasets/` and `ML_DL_Models/scripts/` to regenerate local artifacts.

## Contributing
1. Create a feature branch (`feature/<name>`).
2. Run linting & tests before opening a PR.
3. Include security review notes for any tool/agent touching customer data.

Maintainers: see `docs/ARCHITECTURE.md` for design principles and `docs/AGENTS.md` for per-agent responsibilities.



