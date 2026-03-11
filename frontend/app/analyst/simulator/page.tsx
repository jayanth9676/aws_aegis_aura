import React from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { TransactionForm } from '@/components/simulator/TransactionForm'
import { Activity, Beaker } from 'lucide-react'

export default function SimulatorPage() {
	return (
		<MainLayout>
			<div className="container mx-auto py-8 px-4 max-w-7xl animate-in fade-in zoom-in duration-500 min-h-screen space-y-8">
				<div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-200 dark:border-neutral-800 pb-4">
					<div>
						<h1 className="text-3xl font-extrabold tracking-tight lg:text-4xl text-neutral-900 dark:text-neutral-50 flex items-center">
							<Beaker className="w-8 h-8 mr-3 text-indigo-500" />
							Event Simulator
						</h1>
						<p className="text-muted-foreground mt-2">
							Inject edge cases and anomaly scenarios into the Aegis Orchestrator manually.
						</p>
					</div>
					<div className="flex items-center space-x-2 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
						<Activity className="w-4 h-4 mr-1 animate-pulse" /> Supervisor Online
					</div>
				</div>

				<TransactionForm />

			</div>
		</MainLayout>
	)
}
