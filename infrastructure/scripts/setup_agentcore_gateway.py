"""Provision AgentCore Gateway and register Lambda tool targets."""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from typing import Dict, List, Tuple

from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient


LAMBDA_TOOLS: Dict[str, List[Dict[str, str]]] = {
    "aegis-payment-tools": [
        {
            "name": "TransactionAnalysisTool",
            "description": "Retrieve and analyse historical transactions",
        },
        {
            "name": "PaymentAPITool",
            "description": "Allow, hold, or block a payment",
        },
        {
            "name": "VelocityAnalysisTool",
            "description": "Evaluate transaction velocity anomalies",
        },
    ],
    "aegis-verification-tools": [
        {
            "name": "VerificationOfPayeeTool",
            "description": "Run CoP verification for a payee",
        },
        {
            "name": "WatchlistTool",
            "description": "Check watchlists and sanctions",
        },
    ],
    "aegis-customer-tools": [
        {
            "name": "CustomerAnalysisTool",
            "description": "Analyse customer profile and vulnerability",
        },
        {
            "name": "FraudHistoryTool",
            "description": "Retrieve customer fraud history",
        },
    ],
    "aegis-graph-tools": [
        {
            "name": "GraphAnalysisTool",
            "description": "Perform network graph risk analysis",
        },
        {
            "name": "MuleDetectionTool",
            "description": "Run graph mule detection",
        },
    ],
    "aegis-ml-tools": [
        {
            "name": "FraudDetectionTool",
            "description": "Invoke fraud detection ML ensemble",
        },
        {
            "name": "SHAPExplainerTool",
            "description": "Generate SHAP explanations",
        },
        {
            "name": "BehavioralAnalysisTool",
            "description": "Analyse behavioural biometrics",
        },
        {
            "name": "MuleDetectionTool",
            "description": "Run ML mule detection",
        },
    ],
    "aegis-kb-tools": [
        {
            "name": "KnowledgeBaseTool",
            "description": "Query Bedrock knowledge base",
        },
        {
            "name": "PayeeAnalysisTool",
            "description": "Retrieve payee intelligence",
        },
    ],
    "aegis-case-tools": [
        {
            "name": "EscalationTool",
            "description": "Escalate high risk cases",
        },
        {
            "name": "CaseManagementTool",
            "description": "Create or update investigation case",
        },
        {
            "name": "FeedbackStorageTool",
            "description": "Store analyst feedback",
        },
        {
            "name": "ModelReviewQueueTool",
            "description": "Queue model review tasks",
        },
        {
            "name": "SARStorageTool",
            "description": "Persist SAR artefacts",
        },
    ],
}


def _build_tool_schema(tools: List[Dict[str, str]]) -> List[Dict[str, object]]:
    schema: List[Dict[str, object]] = []
    for tool in tools:
        schema.append(
            {
                "name": tool["name"],
                "description": tool.get("description", tool["name"]),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "payload": {
                            "type": "object",
                            "description": "JSON payload forwarded to the Lambda tool",
                        }
                    },
                    "required": ["payload"],
                },
            }
        )
    return schema


def _create_or_update_gateway(client: GatewayClient, region: str, name: str) -> Dict[str, object]:
    logging.info("Creating OAuth authorizer via Cognito…")
    cognito_response = client.create_oauth_authorizer_with_cognito(name)

    logging.info("Creating AgentCore gateway…")
    gateway = client.create_mcp_gateway(
        name=name,
        authorizer_config=cognito_response["authorizer_config"],
        enable_semantic_search=True,
    )

    logging.info("Waiting for IAM propagation…")
    time.sleep(30)

    return {"gateway": gateway, "cognito": cognito_response}


def _parse_gateway_arn(gateway_arn: str) -> Tuple[str, str]:
    parts = gateway_arn.split(":")
    if len(parts) < 6:
        raise ValueError(f"Invalid gateway ARN: {gateway_arn}")
    return parts[3], parts[4]


def _wait_for_target_ready(control_client, gateway_id: str, target_id: str, max_attempts: int = 60, delay: int = 5) -> None:
    for attempt in range(max_attempts):
        response = control_client.get_gateway_target(
            gatewayIdentifier=gateway_id,
            targetId=target_id,
        )
        status = response.get("status")
        if status == "READY":
            return
        if status == "FAILED":
            raise RuntimeError(f"Target {target_id} failed to provision")
        logging.debug("Target %s status %s (attempt %s/%s)", target_id, status, attempt + 1, max_attempts)
        time.sleep(delay)
    raise TimeoutError(f"Target {target_id} not ready after {max_attempts * delay} seconds")


def _create_lambda_target(
    client: GatewayClient,
    gateway: Dict[str, object],
    region: str,
    account_id: str,
    function_name: str,
    tools: List[Dict[str, str]],
):
    lambda_arn = f"arn:aws:lambda:{region}:{account_id}:function:{function_name}"

    tool_schema = _build_tool_schema(tools)

    logging.info("Creating target for %s", function_name)
    control_client = client.client
    request = {
        "gatewayIdentifier": gateway["gatewayId"],
        "name": function_name,
        "targetConfiguration": {
            "mcp": {
                "lambda": {
                    "lambdaArn": lambda_arn,
                    "toolSchema": {"inlinePayload": tool_schema},
                }
            }
        },
        "credentialProviderConfigurations": [
            {"credentialProviderType": "GATEWAY_IAM_ROLE"}
        ],
    }
    target = control_client.create_gateway_target(**request)
    logging.info("Waiting for target %s to become READY", target["targetId"])
    _wait_for_target_ready(control_client, gateway["gatewayId"], target["targetId"])
    return target


def _attach_lambda_invoke_policy(
    client: GatewayClient,
    gateway: Dict[str, object],
    region: str,
    account_id: str,
    function_names: List[str],
) -> None:
    role_arn = gateway.get("roleArn")
    if not role_arn:
        logging.warning("Gateway role ARN not found; skipping IAM policy update")
        return

    role_name = role_arn.split("/")[-1]
    iam_client = client.session.client("iam")

    resources = []
    for name in function_names:
        base_arn = f"arn:aws:lambda:{region}:{account_id}:function:{name}"
        resources.extend([base_arn, f"{base_arn}:*"])

    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["lambda:InvokeFunction"],
                "Resource": resources,
            }
        ],
    }

    logging.info("Updating gateway role policy for Lambda invocation…")
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName="AgentCoreInvokeAegisTools",
        PolicyDocument=json.dumps(policy_document),
    )


def main(region: str, output: Path, name: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    client = GatewayClient(region_name=region)

    resources = _create_or_update_gateway(client, region, name)
    gateway = resources["gateway"]

    gateway_region, account_id = _parse_gateway_arn(gateway["gatewayArn"])

    targets = []
    for function_name, tool_defs in LAMBDA_TOOLS.items():
        target = _create_lambda_target(client, gateway, gateway_region, account_id, function_name, tool_defs)
        targets.append(target)

    _attach_lambda_invoke_policy(client, gateway, gateway_region, account_id, list(LAMBDA_TOOLS.keys()))

    config = {
        "gateway_url": gateway["gatewayUrl"],
        "gateway_id": gateway["gatewayId"],
        "region": region,
        "client_info": resources["cognito"]["client_info"],
        "targets": targets,
        "gateway_arn": gateway["gatewayArn"],
    }

    output.write_text(json.dumps(config, indent=2, default=str))
    logging.info("Gateway setup complete. Configuration stored at %s", output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup AgentCore Gateway targets for Lambda tools")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--name", default="TestAegisGateway")
    parser.add_argument("--output", default="gateway_config.json")
    args = parser.parse_args()

    main(args.region, Path(args.output).resolve(), args.name)

