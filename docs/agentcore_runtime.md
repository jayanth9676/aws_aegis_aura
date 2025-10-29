# AgentCore Runtime Integration Guide

## Prerequisites
- Ensure `AGENTCORE_MEMORY_ID`, `AGENTCORE_RUNTIME_ARN`, and related env vars are set (see `env.template`)
- Install backend dependencies: `pip install -r backend/requirements.txt`

## Memory Strategy
- Utilizes summary, semantic, and preference strategies via `AgentCoreMemoryManager`
- Supervisor and downstream agents persist intermediate artifacts (context snapshots, analysis, decisions, regulatory outputs) per session
- Fallback key-value storage retained for local development

## Gateway Configuration
- `AGENTCORE_GATEWAY_ENDPOINT` and `AGENTCORE_GATEWAY_ID` enable remote tool invocation
- Set `GATEWAY_CLIENT_ID`, `GATEWAY_CLIENT_SECRET`, `GATEWAY_TOKEN_ENDPOINT`, and optional `GATEWAY_SCOPE` using the output from `infrastructure/scripts/setup_agentcore_gateway.py`
- Script provisions Cognito authorizer, creates Gateway, and registers all Lambda tool targets ([Gateway Quickstart](https://aws.github.io/bedrock-agentcore-starter-toolkit/user-guide/gateway/quickstart.html))
- Access tokens fetched automatically through the starter toolkit client; `GATEWAY_ACCESS_TOKEN` can be used for manual overrides
- Automatically falls back to local tool call if gateway unreachable

## Runtime Entry Point
- `backend/agentcore_entrypoints.py` exposes the `investigate` entrypoint, delegating to the Supervisor agent for full workflow orchestration.
- The Supervisor agent orchestrates: parallel context agents (transaction, customer, payee, behavioral, graph), synthesis/analysis (risk scoring + intel), triage decision, and downstream actions (dialogue, investigation, policy decision, regulatory reporting).
- Investigations are journaled per session via AgentCore Memory and persisted to case management tools (`session:{id}:context_snapshot`, `:risk_assessment`, `:decision_summary`, etc.).
- Configure: `agentcore configure -e backend/agentcore_entrypoints.py`
- Deploy: `agentcore launch`

## Monitoring
- Structured logs through `backend/utils/logging.py`
- CloudWatch / X-Ray instrumentation inherited from existing backend utilities
- Memory events tagged by session IDs for traceability

## Operational Notes
- Execution role requires Bedrock AgentCore memory + gateway permissions
- Store gateway credentials in Secrets Manager when possible
- Align `MEMORY_EVENT_EXPIRY_DAYS`, `MEMORY_TTL_DEFAULT`, `MEMORY_TTL_LONG_TERM` with compliance policies

