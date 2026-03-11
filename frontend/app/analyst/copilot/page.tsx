'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { Send, Bot, User, Loader2, Trash2, Download, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import type { AgentMessage } from '@/types'
import { apiClient } from '@/lib/api-client'

function formatTimestamp(ts: string) {
  return new Date(ts).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: 'system-1',
      role: 'assistant',
      content:
        'Hello! I\'m your AI fraud analyst co-pilot. I can help you investigate cases, explain fraud patterns, interpret risk scores, and guide you through regulatory requirements. What would you like to explore?',
      timestamp: new Date().toISOString(),
      agent_name: 'Aegis AI Co-pilot',
      confidence: 0.98,
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState<string | null>(null)

  const scrollRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // Auto-scroll on new messages
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessage])

  // Connect WebSocket for streaming responses
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
    const socket = new WebSocket(wsUrl)

    socket.onopen = () => {
      setWsConnected(true)
      // Subscribe to copilot stream
      socket.send(JSON.stringify({ type: 'subscribe', id: 'copilot' }))
    }

    socket.onclose = () => setWsConnected(false)
    socket.onerror = () => setWsConnected(false)

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)

        if (msg.type === 'copilot_response_chunk') {
          setStreamingMessage((prev) => (prev ?? '') + msg.chunk)
        }

        if (msg.type === 'copilot_response_complete') {
          const finalContent = msg.full_response
          setStreamingMessage(null)
          setIsLoading(false)
          setMessages((prev) => [
            ...prev,
            {
              id: `assistant-${Date.now()}`,
              role: 'assistant',
              content: finalContent,
              timestamp: new Date().toISOString(),
              agent_name: 'Aegis AI Co-pilot',
              confidence: 0.92,
            },
          ])
        }

        if (msg.type === 'error') {
          setStreamingMessage(null)
          setIsLoading(false)
          setError(msg.message || 'WebSocket error')
        }
      } catch (_) {
        // ignore malformed frames
      }
    }

    wsRef.current = socket

    return () => {
      socket.close()
    }
  }, [])

  const handleSendMessage = useCallback(async () => {
    const content = input.trim()
    if (!content || isLoading) return

    setInput('')
    setError(null)

    const userMessage: AgentMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    // Prefer WebSocket streaming if connected, else fall back to REST
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const allMessages = [...messages, userMessage]
      wsRef.current.send(
        JSON.stringify({
          type: 'copilot_query',
          query: content,
          context: {
            conversation_history: allMessages
              .slice(-6)
              .map((m) => `${m.role}: ${m.content}`),
          },
        })
      )
      // Response handled in onmessage above — setIsLoading will be cleared there
    } else {
      // REST fallback
      try {
        const allMessages = [...messages, userMessage]
        const contextHistory = allMessages
          .slice(-6)
          .map((m) => ({ role: m.role, content: m.content }))

        setStreamingMessage('')
        const fullResponseText = await apiClient.copilotChat(
          contextHistory as any,
          (chunk) => {
            setStreamingMessage((prev) => (prev || '') + chunk)
          }
        ) as string

        setStreamingMessage(null)
        setMessages((prev) => [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: fullResponseText,
            timestamp: new Date().toISOString(),
            agent_name: 'Aegis AI Co-pilot',
            confidence: 0.92,
          },
        ])
      } catch (err: any) {
        setError(err.message || 'Failed to get response. Please try again.')
        setMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: 'assistant',
            content: 'Sorry, I encountered an error. Please try again.',
            timestamp: new Date().toISOString(),
            agent_name: 'Aegis AI Co-pilot',
          },
        ])
      } finally {
        setIsLoading(false)
      }
    }
  }, [input, isLoading, messages])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleClearChat = () => {
    setMessages([
      {
        id: 'system-1',
        role: 'assistant',
        content: 'Chat cleared. How can I help you?',
        timestamp: new Date().toISOString(),
        agent_name: 'Aegis AI Co-pilot',
        confidence: 0.98,
      },
    ])
    setError(null)
  }

  const handleExport = () => {
    const text = messages
      .map((m) => `[${formatTimestamp(m.timestamp)}] ${m.role.toUpperCase()}: ${m.content}`)
      .join('\n\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `aegis-copilot-${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const suggestedQueries = [
    'Explain risk score of 87 for this case',
    'What are the indicators of an investment scam?',
    'When should I file a SAR?',
    'What PSR Consumer Standard requirements apply here?',
  ]

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto px-4 py-4 gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">AI Fraud Analyst Co-pilot</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Powered by AWS Bedrock · Knowledge Base RAG · Strands Agents
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className={cn(
              'gap-1 text-xs',
              wsConnected ? 'text-green-600 border-green-600' : 'text-muted-foreground'
            )}
          >
            {wsConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            {wsConnected ? 'Streaming' : 'REST'}
          </Badge>
          <Button variant="ghost" size="icon" onClick={handleExport} title="Export chat">
            <Download className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleClearChat} title="Clear chat">
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-2 text-sm text-destructive flex items-center justify-between">
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={() => setError(null)}>
            <RefreshCw className="h-3 w-3 mr-1" /> Retry
          </Button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto rounded-xl border bg-muted/20 p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              'flex gap-3',
              msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
            )}
          >
            <div
              className={cn(
                'flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center',
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
              )}
            >
              {msg.role === 'user' ? (
                <User className="h-4 w-4" />
              ) : (
                <Bot className="h-4 w-4" />
              )}
            </div>
            <div
              className={cn(
                'max-w-[80%] rounded-2xl px-4 py-3 text-sm',
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground rounded-tr-sm'
                  : 'bg-background border shadow-sm rounded-tl-sm'
              )}
            >
              <div className="prose prose-sm dark:prose-invert max-w-none break-words leading-relaxed">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.content}
                </ReactMarkdown>
              </div>
              <div className="mt-1.5 flex items-center gap-2 text-xs opacity-60">
                <span>{formatTimestamp(msg.timestamp)}</span>
                {msg.agent_name && msg.role === 'assistant' && (
                  <span>· {msg.agent_name}</span>
                )}
                {msg.confidence !== undefined && msg.role === 'assistant' && (
                  <span>· {(msg.confidence * 100).toFixed(0)}% confident</span>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Streaming indicator */}
        {streamingMessage !== null && (
          <div className="flex gap-3 flex-row">
            <div className="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600 text-white">
              <Bot className="h-4 w-4" />
            </div>
            <div className="max-w-[80%] rounded-2xl p-4 bg-background border shadow-sm rounded-tl-sm text-sm">
              <div className="prose prose-sm dark:prose-invert max-w-none break-words leading-relaxed">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {streamingMessage}
                </ReactMarkdown>
                <span className="inline-block w-1.5 h-4 bg-primary animate-pulse ml-0.5 rounded-sm" />
              </div>
            </div>
          </div>
        )}

        {/* Loading dots (before first chunk arrives) */}
        {isLoading && streamingMessage === null && (
          <div className="flex gap-3 flex-row">
            <div className="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600 text-white">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-2xl rounded-tl-sm px-4 py-3 bg-background border shadow-sm">
              <div className="flex gap-1.5 items-center h-4">
                <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:0ms]" />
                <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:150ms]" />
                <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* Suggested queries (shown when only system message) */}
      {messages.length === 1 && (
        <div className="grid grid-cols-2 gap-2">
          {suggestedQueries.map((q) => (
            <button
              key={q}
              onClick={() => setInput(q)}
              className="text-left text-sm rounded-lg border bg-background px-3 py-2 hover:bg-muted/60 transition-colors text-muted-foreground hover:text-foreground"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex gap-2 items-end relative">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about fraud patterns, cases, regulatory requirements..."
          className="flex-1 resize-none rounded-xl border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary min-h-[52px] max-h-[140px] overflow-y-auto"
          rows={1}
          disabled={isLoading}
        />
        <Button
          onClick={handleSendMessage}
          disabled={!input.trim() || isLoading}
          size="icon"
          className="h-[52px] w-[52px] rounded-xl flex-shrink-0"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  )
}
