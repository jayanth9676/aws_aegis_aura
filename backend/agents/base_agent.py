"""Base agent class for Aegis multi-agent system with AgentCore integration."""

import json
import time
from typing import Any, Dict, Optional, List
from abc import ABC, abstractmethod

from config import aws_config, AgentConfig, system_config
from utils import get_logger, metrics_tracker, trace_operation, add_trace_metadata
from agentcore.memory_manager import AgentCoreMemoryManager
from agentcore.gateway_client import AgentCoreGatewayClient
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole


class AegisBaseAgent(ABC):
    """Base class for all Aegis agents with AgentCore integration."""
    
    def __init__(self, name: str, config: AgentConfig):
        self.name = name
        self.config = config
        self.logger = get_logger(f"agent.{name}")
        
        # AWS clients
        self.bedrock = aws_config.bedrock_runtime
        self.bedrock_agent = aws_config.bedrock_agent_runtime

        # AgentCore components
        self.memory = AgentCoreMemoryManager(self.logger)
        self.gateway = AgentCoreGatewayClient(self.logger)
        
        # Guardrails
        self.guardrails_id = config.guardrails_id
        self.guardrails_version = config.guardrails_version
        
        self.logger.info(f"Initialized agent: {name}", agent=name)
    
    async def invoke_tool(self, tool_name: str, params: Dict) -> Dict:
        """Invoke tool via AgentCore Gateway."""
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Invoking tool: {tool_name}",
                agent=self.name,
                tool=tool_name,
                params=params
            )
            
            result = await self.gateway.invoke(tool_name, params)
            
            latency_ms = (time.time() - start_time) * 1000
            self.logger.info(
                f"Tool invocation completed: {tool_name}",
                agent=self.name,
                tool=tool_name,
                latency_ms=latency_ms
            )
            
            add_trace_metadata(f'{tool_name}_result', result)
            
            return result
        except Exception as e:
            self.logger.error(
                f"Tool invocation failed: {tool_name}",
                agent=self.name,
                tool=tool_name,
                error=str(e)
            )
            return {'error': str(e)}
    
    async def store_memory(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in AgentCore Memory."""
        ttl = ttl or self.config.session_ttl
        return await self.memory.put(key, value, ttl)
    
    async def retrieve_memory(self, key: str) -> Optional[Any]:
        """Retrieve value from AgentCore Memory."""
        return await self.memory.get(key)
    
    async def delete_memory(self, key: str) -> bool:
        """Delete value from AgentCore Memory."""
        return await self.memory.delete(key)

    async def record_session_messages(
        self,
        session_id: str,
        messages: List[ConversationalMessage],
        actor_id: Optional[str] = None
    ) -> None:
        await self.memory.record_session_turn(
            session_id=session_id,
            messages=messages,
            actor_id=actor_id or self.name
        )

    async def record_text_message(
        self,
        session_id: str,
        content: str,
        role: MessageRole = MessageRole.ASSISTANT,
        actor_id: Optional[str] = None
    ) -> None:
        message = ConversationalMessage(content, role)
        await self.record_session_messages(session_id, [message], actor_id)

    async def record_investigation_summary(self, session_id: str, summary: Dict[str, Any]) -> None:
        await self.memory.record_investigation_summary(
            session_id=session_id,
            summary=summary,
            actor_id=self.name
        )
    
    async def invoke_bedrock(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Invoke Bedrock model with optional Guardrails."""
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        messages = [{'role': 'user', 'content': prompt}]
        
        body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': self.config.top_p
        }
        
        if system_prompt:
            body['system'] = system_prompt
        
        try:
            # Invoke with Guardrails if configured
            if self.guardrails_id:
                response = self.bedrock.invoke_model(
                    modelId=self.config.model_id,
                    guardrailIdentifier=self.guardrails_id,
                    guardrailVersion=self.guardrails_version,
                    body=json.dumps(body),
                    contentType='application/json'
                )
            else:
                response = self.bedrock.invoke_model(
                    modelId=self.config.model_id,
                    body=json.dumps(body),
                    contentType='application/json'
                )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
        
        except Exception as e:
            self.logger.error(
                f"Bedrock invocation failed",
                agent=self.name,
                error=str(e)
            )
            raise
    
    async def reason_with_bedrock(self, prompt: str, context: Dict, output_format: str = 'json') -> Dict:
        """Use Bedrock Claude for AI reasoning with structured output."""
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._format_prompt_with_context(prompt, context)
        
        # Add JSON formatting instruction if needed
        if output_format == 'json':
            user_prompt += "\n\nProvide your response as valid JSON only, with no additional text."
        
        try:
            response_text = await self.invoke_bedrock(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2000
            )
            
            # Parse structured output
            if output_format == 'json':
                return self._parse_ai_response(response_text)
            else:
                return {'response': response_text}
        
        except Exception as e:
            self.logger.error(
                f"AI reasoning failed",
                agent=self.name,
                error=str(e)
            )
            # Return fallback response
            return {'error': str(e), 'fallback': True}
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for the agent."""
        return f"""You are {self.name}, an AI agent in the Aegis fraud prevention system.

Your role: {self.config.description if hasattr(self.config, 'description') else 'Fraud analysis'}

Guidelines:
- Analyze data objectively and thoroughly
- Identify fraud risk factors with clear reasoning
- Provide structured, actionable insights
- Be concise but comprehensive
- Focus on evidence-based conclusions"""
    
    def _format_prompt_with_context(self, prompt: str, context: Dict) -> str:
        """Format prompt with context data."""
        context_str = json.dumps(context, indent=2, default=str)
        return f"""Context Data:
{context_str}

Task:
{prompt}"""
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse AI response into structured format."""
        try:
            # Try to extract JSON from response
            import re
            
            # Look for JSON block
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            
            # If no JSON found, try parsing the whole response
            return json.loads(response_text)
        
        except json.JSONDecodeError as e:
            self.logger.warning(
                f"Failed to parse AI response as JSON",
                agent=self.name,
                response=response_text[:200],
                error=str(e)
            )
            # Return text response wrapped in dict
            return {
                'response': response_text,
                'parsed': False
            }
    
    async def query_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict]:
        """Query Bedrock Knowledge Base."""
        try:
            # Check if knowledge base ID is available
            if not system_config.KNOWLEDGE_BASE_ID:
                # Return fallback intelligence for development
                return self._get_fallback_intelligence(query)
            
            response = self.bedrock_agent.retrieve(
                knowledgeBaseId=system_config.KNOWLEDGE_BASE_ID,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': top_k
                    }
                }
            )
            
            documents = [{
                'content': r['content']['text'],
                'source': r.get('location', {}).get('s3Location', {}).get('uri', 'unknown'),
                'score': r.get('score', 0.0)
            } for r in response.get('retrievalResults', [])]
            
            return documents
        except Exception as e:
            self.logger.error(
                f"Knowledge base query failed",
                agent=self.name,
                query=query,
                error=str(e)
            )
            # Return fallback intelligence on error
            return self._get_fallback_intelligence(query)
    
    def _get_fallback_intelligence(self, query: str) -> List[Dict]:
        """Provide fallback intelligence when knowledge base is unavailable."""
        query_lower = query.lower()
        
        if 'impersonation' in query_lower:
            return [{
                'content': 'Impersonation fraud involves perpetrators assuming false identities to deceive victims. Key indicators include unsolicited contact, urgent requests, mismatched communication channels, and pressure tactics. Investigate by verifying identity through independent channels and analyzing communication metadata.',
                'source': 'fallback_intelligence',
                'score': 0.9
            }]
        elif 'investment' in query_lower or 'romance' in query_lower:
            return [{
                'content': 'Investment and romance scams target victims through emotional manipulation and false promises of returns. Red flags include unsolicited investment opportunities, pressure to act quickly, requests for large amounts, and promises of guaranteed returns. Verify all investment opportunities through legitimate channels.',
                'source': 'fallback_intelligence',
                'score': 0.9
            }]
        elif 'invoice' in query_lower or 'redirection' in query_lower:
            return [{
                'content': 'Invoice redirection fraud involves intercepting legitimate business communications to redirect payments to fraudulent accounts. Indicators include changes to payment details, urgent requests to update banking information, and mismatched payee names. Always verify payment changes through established channels.',
                'source': 'fallback_intelligence',
                'score': 0.9
            }]
        elif 'mule' in query_lower or 'money laundering' in query_lower:
            return [{
                'content': 'Money mule networks use intermediary accounts to launder funds and obscure transaction trails. Patterns include rapid movement of funds, multiple small transactions, circular flows, and accounts with no legitimate business purpose. Monitor for unusual network patterns and rapid fund movement.',
                'source': 'fallback_intelligence',
                'score': 0.9
            }]
        else:
            return [{
                'content': 'Authorized Push Payment (APP) fraud involves deceiving victims into authorizing payments to fraudulent accounts. Common indicators include urgency, emotional manipulation, new payees, large amounts, and behavioral anomalies. Always verify payee details and be cautious of high-pressure tactics.',
                'source': 'fallback_intelligence',
                'score': 0.8
            }]
    
    @trace_operation("agent_invoke")
    async def invoke_agent(self, agent_name: str, params: Dict) -> Dict:
        """Invoke another agent (for agent-to-agent communication)."""
        # This would be implemented to invoke other agents via AgentCore
        # For now, placeholder
        self.logger.info(
            f"Invoking agent: {agent_name}",
            source_agent=self.name,
            target_agent=agent_name
        )
        return {'status': 'agent_invocation_placeholder'}
    
    @abstractmethod
    async def execute(self, input_data: Dict) -> Dict:
        """Execute agent logic. Must be implemented by subclasses."""
        pass
    
    async def __call__(self, input_data: Dict) -> Dict:
        """Make agent callable."""
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Agent execution started",
                agent=self.name,
                input_data=input_data
            )
            
            add_trace_metadata('agent_name', self.name)
            add_trace_metadata('input_data', input_data)
            
            result = await self.execute(input_data)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Track metrics
            metrics_tracker.track_agent_performance(
                self.name,
                success=True,
                latency_ms=latency_ms
            )
            
            self.logger.info(
                f"Agent execution completed",
                agent=self.name,
                latency_ms=latency_ms,
                success=True
            )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            metrics_tracker.track_agent_performance(
                self.name,
                success=False,
                latency_ms=latency_ms
            )
            
            self.logger.error(
                f"Agent execution failed",
                agent=self.name,
                error=str(e),
                latency_ms=latency_ms
            )
            
            return {
                'success': False,
                'error': str(e),
                'agent': self.name
            }



