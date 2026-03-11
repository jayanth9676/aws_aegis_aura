'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { apiClient } from '@/lib/api-client'
import { Bot, Play, ShieldAlert, CheckCircle, HelpCircle } from 'lucide-react'

export function TransactionForm() {
	const [formData, setFormData] = useState({
		transaction_id: 'SIM-' + Math.floor(Math.random() * 1000000),
		customer_id: 'C-7742',
		amount: '15000',
		payee_account: '88192301',
		payee_name: 'Unknown Crypto Exchange',
		sender_account: '10924012',
		device_fingerprint: 'device_99482'
	})

	// The result from AgentCore
	const [result, setResult] = useState<any>(null)
	const [loading, setLoading] = useState(false)

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault()
		setLoading(true)
		setResult(null)

		try {
			const response = await apiClient.submitTransaction({
				...formData,
				amount: parseFloat(formData.amount),
				session_data: { simulated: true }
			})
			setResult(response)
		} catch (err) {
			console.error(err)
			setResult({ action: 'ERROR', error: 'Failed to contact AgentCore API' })
		} finally {
			setLoading(false)
		}
	}

	const getActionIcon = (action: string) => {
		if (action === 'ALLOW') return <CheckCircle className="w-6 h-6 text-green-500" />
		if (action === 'BLOCK') return <ShieldAlert className="w-6 h-6 text-red-500" />
		if (action === 'CHALLENGE') return <HelpCircle className="w-6 h-6 text-yellow-500" />
		return <Bot className="w-6 h-6 text-gray-500" />
	}

	return (
		<div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
			<Card className="shadow-lg border-neutral-200">
				<CardHeader className="bg-neutral-50 border-b">
					<CardTitle>Transaction Injection Payload</CardTitle>
					<CardDescription>Simulate a raw payment event hitting the Aegis webhook</CardDescription>
				</CardHeader>
				<CardContent className="mt-6">
					<form onSubmit={handleSubmit} className="space-y-4">
						<div className="grid grid-cols-2 gap-4">
							<div className="space-y-2">
								<Label>Transaction ID</Label>
								<Input value={formData.transaction_id} onChange={(e) => setFormData({ ...formData, transaction_id: e.target.value })} />
							</div>
							<div className="space-y-2">
								<Label>Customer ID</Label>
								<Input value={formData.customer_id} onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })} />
							</div>
						</div>

						<div className="space-y-2">
							<Label>Amount (GBP)</Label>
							<Input type="number" value={formData.amount} onChange={(e) => setFormData({ ...formData, amount: e.target.value })} />
						</div>

						<div className="grid grid-cols-2 gap-4">
							<div className="space-y-2">
								<Label>Payee Account</Label>
								<Input value={formData.payee_account} onChange={(e) => setFormData({ ...formData, payee_account: e.target.value })} />
							</div>
							<div className="space-y-2">
								<Label>Payee Name</Label>
								<Input value={formData.payee_name} onChange={(e) => setFormData({ ...formData, payee_name: e.target.value })} />
							</div>
						</div>

						<Button type="submit" className="w-full mt-4" disabled={loading}>
							{loading ? (
								<span className="flex items-center"><span className="animate-spin mr-2 border-t-2 border-white w-4 h-4 rounded-full"></span> Orchestrating...</span>
							) : (
								<span className="flex items-center"><Play className="w-4 h-4 mr-2" /> Inject into Core</span>
							)}
						</Button>
					</form>
				</CardContent>
			</Card>

			<Card className="shadow-lg border-neutral-200 bg-neutral-900 text-white overflow-hidden relative">
				<CardHeader className="bg-neutral-950 border-b border-neutral-800">
					<CardTitle className="text-neutral-100 flex items-center">
						<Bot className="w-5 h-5 mr-2 text-indigo-400" />
						AgentCore Response
					</CardTitle>
					<CardDescription className="text-neutral-400">Synchronous Supervisor Decision</CardDescription>
				</CardHeader>
				<CardContent className="mt-6 flex flex-col items-center justify-center min-h-[300px]">
					{!result && !loading && (
						<div className="text-neutral-500 opacity-50 flex flex-col items-center space-y-2 border border-dashed border-neutral-700 p-8 rounded-xl w-full text-center">
							<Bot className="w-12 h-12" />
							<p>Waiting for payload injection</p>
						</div>
					)}

					{loading && (
						<div className="flex flex-col items-center space-y-4">
							<div className="relative">
								<div className="w-16 h-16 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
								<div className="w-10 h-10 border-4 border-purple-500/30 border-b-purple-500 rounded-full animate-spin absolute top-3 left-3 flex items-center justify-center animation-delay-150"></div>
							</div>
							<p className="text-sm font-mono text-indigo-300">Evaluating swarm concensus...</p>
						</div>
					)}

					{result && !loading && (
						<div className="w-full space-y-6 animate-in slide-in-from-bottom-4">
							<div className="flex items-center justify-center space-x-4 bg-neutral-950 p-6 rounded-2xl border border-neutral-800">
								{getActionIcon(result.action || result.decision)}
								<div>
									<h3 className="text-2xl font-bold uppercase tracking-wider">{result.action || result.decision}</h3>
								</div>
							</div>

							<div className="grid grid-cols-2 gap-4">
								<div className="bg-neutral-800 p-4 rounded-xl">
									<p className="text-xs text-neutral-400 uppercase tracking-widest font-bold">Risk Score</p>
									<p className="text-3xl font-mono mt-1 text-indigo-400">{result.risk_score || 'N/A'}</p>
								</div>
								<div className="bg-neutral-800 p-4 rounded-xl">
									<p className="text-xs text-neutral-400 uppercase tracking-widest font-bold">Confidence</p>
									<p className="text-3xl font-mono mt-1 text-purple-400">{result.confidence ? (result.confidence * 100).toFixed(1) + '%' : 'N/A'}</p>
								</div>
							</div>

							{result.reason_codes && result.reason_codes.length > 0 && (
								<div className="bg-neutral-800 p-4 rounded-xl">
									<p className="text-xs text-neutral-400 uppercase tracking-widest font-bold mb-2">Triggered Rules & Context</p>
									<ul className="space-y-1">
										{result.reason_codes.map((rc: string, i: number) => (
											<li key={i} className="text-sm font-mono text-red-300 bg-red-950/30 px-2 py-1 rounded inline-block">#{rc}</li>
										))}
									</ul>
								</div>
							)}
						</div>
					)}
				</CardContent>
			</Card>
		</div>
	)
}
