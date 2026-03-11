import React from 'react'
import { AgentThoughtStream } from '@/components/analyst/agents/AgentThoughtStream'
import { AgentStatusDashboard } from '@/components/analyst/agents/AgentStatusDashboard'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MainLayout } from '@/components/layout/MainLayout'

export default function AgentsPage() {
	return (
		<MainLayout>
			<div className="container mx-auto py-8 px-4 max-w-7xl animate-in fade-in zoom-in duration-500 min-h-screen space-y-8">
				<div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
					<div>
						<h1 className="text-3xl font-extrabold tracking-tight lg:text-4xl text-neutral-900 dark:text-neutral-50">
							Agent Operations Center
						</h1>
						<p className="text-muted-foreground mt-2">
							Monitor, debug, and trace the cognitive steps of the Aegis Agent Swarm.
						</p>
					</div>
				</div>

				<Tabs defaultValue="overview" className="space-y-6">
					<TabsList className="bg-neutral-100 dark:bg-neutral-900 p-1 rounded-lg">
						<TabsTrigger value="overview" className="rounded-md">Swarm Overview</TabsTrigger>
						<TabsTrigger value="stream" className="rounded-md">Live Stream</TabsTrigger>
						<TabsTrigger value="logs" className="rounded-md">Audit Logs</TabsTrigger>
					</TabsList>
					<TabsContent value="overview" className="space-y-6">
						<AgentStatusDashboard />
					</TabsContent>
					<TabsContent value="stream" className="space-y-6">
						<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
							<AgentThoughtStream />
							<Card className="h-[400px] border-neutral-200 shadow-sm flex flex-col justify-center items-center text-center p-8 bg-neutral-50 dark:bg-neutral-900">
								<CardHeader>
									<CardTitle>Topology Map</CardTitle>
									<CardDescription>Visualizing agent execution paths</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="mt-4 rounded-xl border border-dashed border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-950 p-12 text-neutral-500">
										<p>Agent Topology visualization is coming soon.</p>
									</div>
								</CardContent>
							</Card>
						</div>
					</TabsContent>
					<TabsContent value="logs">
						<Card>
							<CardHeader>
								<CardTitle>Decision Audit Logs</CardTitle>
								<CardDescription>Historical trace of all agent cognitive decisions</CardDescription>
							</CardHeader>
							<CardContent>
								<div className="rounded-md border p-8 text-center text-neutral-500 bg-neutral-50 dark:bg-neutral-900 line-clamp-2">
									Audit Logs module requires the 'system_admin' role. Contact support.
								</div>
							</CardContent>
						</Card>
					</TabsContent>
				</Tabs>
			</div>
		</MainLayout>
	)
}
