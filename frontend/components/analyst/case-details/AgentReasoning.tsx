'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Brain, Database, BarChart3, Shield, Clock } from 'lucide-react'
import type { AgentReasoning as AgentReasoningType } from '@/types'
import { cn } from '@/lib/utils'

interface AgentReasoningProps {
  reasoning: AgentReasoningType[]
}

function getAgentIcon(type: AgentReasoningType['agent_type']) {
  switch (type) {
    case 'CONTEXT':
      return <Database className="h-4 w-4" />
    case 'ANALYSIS':
      return <BarChart3 className="h-4 w-4" />
    case 'DECISION':
      return <Shield className="h-4 w-4" />
    default:
      return <Brain className="h-4 w-4" />
  }
}

function getAgentColor(type: AgentReasoningType['agent_type']) {
  switch (type) {
    case 'CONTEXT':
      return 'text-blue-600 bg-blue-100'
    case 'ANALYSIS':
      return 'text-purple-600 bg-purple-100'
    case 'DECISION':
      return 'text-red-600 bg-red-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

export function AgentReasoning({ reasoning }: AgentReasoningProps) {
  // Sort by agent type: CONTEXT → ANALYSIS → DECISION
  const typeOrder = { CONTEXT: 1, ANALYSIS: 2, DECISION: 3 }
  const sortedReasoning = [...reasoning].sort((a, b) => 
    typeOrder[a.agent_type] - typeOrder[b.agent_type]
  )

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-primary" />
          <div>
            <CardTitle>Agent Reasoning Chain</CardTitle>
            <CardDescription>AI agent analysis and decision making</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" className="w-full">
          {sortedReasoning.map((agent, index) => (
            <AccordionItem key={index} value={`agent-${index}`}>
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-center gap-3 flex-1 text-left">
                  <div className={cn(
                    'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full',
                    getAgentColor(agent.agent_type)
                  )}>
                    {getAgentIcon(agent.agent_type)}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">{agent.agent_name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge variant="outline" className="text-xs">
                        {agent.agent_type}
                      </Badge>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {agent.execution_time_ms}ms
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Confidence: {(agent.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <Badge 
                      variant={
                        agent.risk_contribution >= 20 ? 'destructive' :
                        agent.risk_contribution >= 10 ? 'default' :
                        'secondary'
                      }
                    >
                      +{agent.risk_contribution} risk
                    </Badge>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="pl-11 space-y-4 pt-2">
                  {/* Key Findings */}
                  <div>
                    <p className="text-sm font-medium mb-2">Key Findings</p>
                    <ul className="space-y-1 list-disc list-inside">
                      {agent.findings.map((finding, i) => (
                        <li key={i} className="text-sm text-muted-foreground">
                          {finding}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Raw Data */}
                  {agent.raw_data && Object.keys(agent.raw_data).length > 0 && (
                    <details className="group">
                      <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground list-none">
                        <span className="inline-flex items-center gap-1">
                          <span className="group-open:rotate-90 transition-transform inline-block">
                            ▶
                          </span>
                          View raw data
                        </span>
                      </summary>
                      <div className="mt-2 rounded-md bg-muted p-3">
                        <pre className="text-xs overflow-auto max-h-64">
                          {JSON.stringify(agent.raw_data, null, 2)}
                        </pre>
                      </div>
                    </details>
                  )}

                  {/* Timestamp */}
                  <p className="text-xs text-muted-foreground">
                    Executed at: {new Date(agent.timestamp).toLocaleString()}
                  </p>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>

        {/* Empty State */}
        {sortedReasoning.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Brain className="h-12 w-12 text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">No agent reasoning available</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

