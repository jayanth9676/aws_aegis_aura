'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { BrainCircuit, Activity, Server, Loader2 } from 'lucide-react'

interface ThoughtLine {
  id: string
  agent: string
  message: string
  timestamp: string
  status: 'thinking' | 'done' | 'error'
}

export function AgentThoughtStream() {
  const [thoughts, setThoughts] = useState<ThoughtLine[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  
  // Simulating connection to backend WebSocket
  useEffect(() => {
    // In actual implementation, this will connect to wss://...
    // For now, we simulate the "streaming" of thoughts for demo purposes
    setIsConnected(true)
    
    const demoThoughts = [
      { agent: 'Supervisor', msg: 'Intercepted new transaction request TXN-99812' },
      { agent: 'Supervisor', msg: 'Delegating to Context Agents for enrichment' },
      { agent: 'CustomerContext', msg: 'Fetching 30-day history for Customer C-8841' },
      { agent: 'TransactionContext', msg: 'Analyzing device fingerprint and IP' },
      { agent: 'PayeeContext', msg: 'Flagging new payee - account age < 2 hours' },
      { agent: 'GraphRelationship', msg: 'Mapping 2nd-degree connections. High density of flagged nodes.' },
      { agent: 'RiskScoring', msg: 'Calculating aggregate risk vector... Score: 87/100' },
      { agent: 'Intel', msg: 'Correlating with live threat feeds. Pattern matches "Active Call Scam"' },
      { agent: 'Triage', msg: 'Recommendation: CHALLENGE and trigger DialogueAgent' },
      { agent: 'Supervisor', msg: 'Executing CHALLENGE protocol' }
    ]

    let currentIndex = 0
    const interval = setInterval(() => {
      if (currentIndex < demoThoughts.length) {
        const t = demoThoughts[currentIndex]
        setThoughts(prev => [...prev.slice(-15), {
          id: Math.random().toString(36),
          agent: t.agent,
          message: t.msg,
          timestamp: new Date().toISOString(),
          status: 'done'
        }])
        currentIndex++
      } else {
        clearInterval(interval)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [thoughts])

  return (
    <Card className="w-full flex flex-col h-[400px]">
      <CardHeader className="flex flex-row items-center justify-between pb-2 border-b">
        <div className="flex items-center space-x-2">
          <BrainCircuit className="w-5 h-5 text-indigo-500" />
          <CardTitle className="text-sm font-medium">Agent Neural Stream</CardTitle>
        </div>
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <Badge variant="outline" className="text-green-500 border-green-500/20 bg-green-500/10">
              <Activity className="w-3 h-3 mr-1 animate-pulse" /> Live
            </Badge>
          ) : (
            <Badge variant="outline" className="text-gray-500">
              Connecting...
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-sm bg-neutral-950 text-neutral-300">
        {thoughts.map((t) => (
          <div key={t.id} className="flex flex-col space-y-1 opacity-90 animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-center text-xs opacity-50">
              <span>{new Date(t.timestamp).toLocaleTimeString()}</span>
              <span className="mx-2">•</span>
              <span className="text-indigo-400 font-bold">[{t.agent}]</span>
            </div>
            <div className="pl-2 border-l-2 border-indigo-500/30">
              {t.message}
            </div>
          </div>
        ))}
        {thoughts.length < 10 && (
          <div className="flex items-center space-x-2 text-neutral-500 pt-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-xs">Processing...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </CardContent>
    </Card>
  )
}
