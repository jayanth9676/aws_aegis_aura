'use client'

import React, { useState } from 'react'
import { MessageSquare, X, Send, Command, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api-client'
import { AgentMessage } from '@/types'
import { Card } from '../ui/card'

export function SystemCopilotDrawer() {
	const [isOpen, setIsOpen] = useState(false)
	const [query, setQuery] = useState('')
	const [messages, setMessages] = useState<{ role: 'user' | 'agent', text: string }[]>([])
	const [loading, setLoading] = useState(false)

	const toggleDrawer = () => setIsOpen(!isOpen)

	const handleSend = async (e: React.FormEvent) => {
		e.preventDefault()
		if (!query.trim()) return

		const userMessage = query.trim()
		setMessages(prev => [...prev, { role: 'user', text: userMessage }])
		setQuery('')
		setLoading(true)

		try {
			const response = await apiClient.copilotQuery(userMessage, { /* current context */ })
			setMessages(prev => [...prev, { role: 'agent', text: response.content || 'I am processing your request through the Copilot endpoint.' }])
		} catch (err) {
			setMessages(prev => [...prev, { role: 'agent', text: 'Sorry, I failed to reach the AgentCore backend.' }])
		} finally {
			setLoading(false)
		}
	}

	return (
		<>
			<button
				onClick={toggleDrawer}
				className={cn(
					"fixed bottom-6 right-6 z-50 p-4 rounded-full shadow-lg transition-transform",
					"bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800",
					"hover:scale-105 active:scale-95 group",
					isOpen ? "translate-y-24 opacity-0" : "translate-y-0 opacity-100"
				)}
			>
				<div className="relative">
					<Command className="w-6 h-6 text-indigo-600 dark:text-indigo-400 group-hover:hidden" />
					<MessageSquare className="w-6 h-6 text-indigo-600 dark:text-indigo-400 hidden group-hover:block" />
					<span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-white dark:border-neutral-900"></span>
				</div>
			</button>

			{/* Drawer Overlay */}
			<div
				className={cn(
					"fixed inset-0 z-40 bg-neutral-900/20 backdrop-blur-sm transition-opacity",
					isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
				)}
				onClick={() => setIsOpen(false)}
			/>

			{/* Drawer Panel */}
			<div
				className={cn(
					"fixed top-0 right-0 z-50 h-full w-full max-w-sm sm:max-w-md bg-white dark:bg-neutral-900 shadow-2xl transition-transform duration-300 ease-out border-l border-neutral-200 dark:border-neutral-800 flex flex-col",
					isOpen ? "translate-x-0" : "translate-x-full"
				)}
			>
				<div className="flex items-center justify-between p-4 border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-950/50">
					<div className="flex items-center space-x-2">
						<Command className="w-5 h-5 text-indigo-500" />
						<h2 className="font-semibold text-neutral-900 dark:text-neutral-100">Intelligent Copilot</h2>
					</div>
					<button onClick={() => setIsOpen(false)} className="p-2 rounded-full hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-colors">
						<X className="w-5 h-5 text-neutral-500" />
					</button>
				</div>

				<div className="flex-1 overflow-y-auto p-4 space-y-4">
					{messages.length === 0 && (
						<div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50">
							<MessageSquare className="w-12 h-12 text-indigo-300" />
							<p className="text-sm">Ask me anything about active cases, anomalies, or to draft emails.</p>
						</div>
					)}
					{messages.map((m, i) => (
						<div key={i} className={cn("flex flex-col max-w-[85%]", m.role === 'user' ? "ml-auto" : "mr-auto")}>
							<div className={cn(
								"p-3 rounded-2xl text-sm shadow-sm",
								m.role === 'user'
									? "bg-indigo-600 text-white rounded-br-none"
									: "bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 rounded-bl-none"
							)}>
								{m.text}
							</div>
						</div>
					))}
					{loading && (
						<div className="flex flex-col mr-auto max-w-[85%]">
							<div className="p-4 rounded-2xl text-sm shadow-sm bg-neutral-100 dark:bg-neutral-800 rounded-bl-none flex items-center space-x-2">
								<Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
								<span className="text-neutral-500">Agent thinking...</span>
							</div>
						</div>
					)}
				</div>

				<div className="p-4 border-t border-neutral-200 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-950/50">
					<form onSubmit={handleSend} className="relative flex items-center">
						<input
							type="text"
							value={query}
							onChange={(e) => setQuery(e.target.value)}
							placeholder="Ask Copilot (e.g. 'Draft email to C-8841')..."
							className="w-full bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-full pl-4 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-shadow disabled:opacity-50"
							disabled={loading}
						/>
						<button
							type="submit"
							disabled={!query.trim() || loading}
							className="absolute right-2 p-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full transition-colors disabled:opacity-50 disabled:hover:bg-indigo-600"
						>
							<Send className="w-4 h-4" />
						</button>
					</form>
					<div className="text-center mt-2">
						<span className="text-[10px] text-neutral-400 uppercase tracking-widest font-bold">Powered by AgentCore</span>
					</div>
				</div>
			</div>
		</>
	)
}
