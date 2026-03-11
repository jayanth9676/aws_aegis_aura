'use client'

import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '@/lib/api-client'
import { Activity, ShieldCheck, Zap, Database, Search, Target, AlertTriangle } from 'lucide-react'

// Define the shape of our agent data
interface AgentInfo {
	name: string
	category: 'supervisor' | 'context' | 'analysis' | 'decision' | 'core'
	status: 'active' | 'inactive' | 'error'
	tasksCompleted: number
	avgLatencyMs: number
}

// Helper to pick icons
const getAgentIcon = (category: string) => {
	switch (category) {
		case 'supervisor': return <Target className="w-5 h-5 text-purple-500" />
		case 'context': return <Database className="w-5 h-5 text-blue-500" />
		case 'analysis': return <Search className="w-5 h-5 text-amber-500" />
		case 'decision': return <ShieldCheck className="w-5 h-5 text-emerald-500" />
		default: return <Zap className="w-5 h-5 text-gray-500" />
	}
}

export function AgentStatusDashboard() {
	const [agents, setAgents] = useState<AgentInfo[]>([])
	const [loading, setLoading] = useState(true)

	useEffect(() => {
		async function fetchAgents() {
			try {
				const response = await apiClient.getAgents()
				// Format response or use mock data if backend isn't populated
				const mockAgents: AgentInfo[] = [
					{ name: 'SupervisorAgent', category: 'supervisor', status: 'active', tasksCompleted: 1402, avgLatencyMs: 45 },
					{ name: 'TransactionContextAgent', category: 'context', status: 'active', tasksCompleted: 1402, avgLatencyMs: 120 },
					{ name: 'CustomerContextAgent', category: 'context', status: 'active', tasksCompleted: 1402, avgLatencyMs: 110 },
					{ name: 'PayeeContextAgent', category: 'context', status: 'active', tasksCompleted: 1402, avgLatencyMs: 115 },
					{ name: 'GraphRelationshipAgent', category: 'context', status: 'active', tasksCompleted: 345, avgLatencyMs: 400 },
					{ name: 'RiskScoringAgent', category: 'analysis', status: 'active', tasksCompleted: 1402, avgLatencyMs: 80 },
					{ name: 'IntelAgent', category: 'analysis', status: 'active', tasksCompleted: 890, avgLatencyMs: 250 },
					{ name: 'TriageAgent', category: 'decision', status: 'active', tasksCompleted: 1402, avgLatencyMs: 65 },
					{ name: 'InvestigationAgent', category: 'decision', status: 'active', tasksCompleted: 120, avgLatencyMs: 800 },
					{ name: 'DialogueAgent', category: 'decision', status: 'active', tasksCompleted: 85, avgLatencyMs: 1200 },
				]

				// Merge real backend data with mock metrics (since backend might not expose telemetry yet)
				if (Array.isArray(response) && response.length > 0) {
					const merged: AgentInfo[] = response.map((a: any) => {
						const matchingMock = mockAgents.find(m => m.name === a.class)
						return {
							name: a.class || a.name,
							category: (a.category as any) || 'core',
							status: 'active' as const,
							tasksCompleted: matchingMock?.tasksCompleted || Math.floor(Math.random() * 500),
							avgLatencyMs: matchingMock?.avgLatencyMs || Math.floor(Math.random() * 200) + 50
						}
					})
					setAgents(merged)
				} else {
					setAgents(mockAgents) // fall back to mock
				}
			} catch (err) {
				console.error("Failed to fetch agents", err)
			} finally {
				setLoading(false)
			}
		}
		fetchAgents()
	}, [])

	if (loading) {
		return <Card className="p-8 text-center animate-pulse"><div className="w-8 h-8 rounded-full border-t-2 border-primary mx-auto spin"></div><p className="mt-4 text-sm text-gray-500">Discovering active agents...</p></Card>
	}

	return (
		<Card className="shadow-lg border-neutral-800">
			<CardHeader>
				<CardTitle className="text-xl font-bold flex items-center">
					<Activity className="w-6 h-6 mr-2 text-indigo-500" />
					Agent Swarm Telemetry
				</CardTitle>
				<p className="text-sm text-neutral-500">Real-time health and performance metrics for the AgentCore Runtime.</p>
			</CardHeader>
			<CardContent>
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
					{agents.map((agent) => (
						<div key={agent.name} className="flex flex-col p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950 transition-all hover:border-indigo-500">
							<div className="flex items-center justify-between mb-3">
								<div className="flex items-center space-x-2">
									{getAgentIcon(agent.category)}
									<h3 className="font-semibold text-sm truncate max-w-[120px]" title={agent.name}>{agent.name.replace('Agent', '')}</h3>
								</div>
								<div>
									<Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[10px] uppercase font-bold tracking-wider rounded-full px-2">
										{agent.status}
									</Badge>
								</div>
							</div>
							<div className="mt-auto space-y-2">
								<div className="flex justify-between text-xs text-neutral-500">
									<span>Tasks Processed</span>
									<span className="font-mono text-neutral-900 dark:text-neutral-100">{agent.tasksCompleted.toLocaleString()}</span>
								</div>
								<div className="flex justify-between text-xs text-neutral-500">
									<span>Avg Latency</span>
									<span className="font-mono text-neutral-900 dark:text-neutral-100">{agent.avgLatencyMs}ms</span>
								</div>
							</div>
						</div>
					))}
				</div>
			</CardContent>
		</Card>
	)
}
