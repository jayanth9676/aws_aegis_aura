'use client'

import { useState } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { ChatInput } from '@/components/analyst/copilot/ChatInput'
import { ContextPanel } from '@/components/analyst/copilot/ContextPanel'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Brain, User, Sparkles, Download, Trash2 } from 'lucide-react'
import type { AgentMessage } from '@/types'

export default function CopilotPage() {
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const handleSendMessage = async (content: string) => {
    const userMessage: AgentMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: AgentMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I understand you're asking about "${content}". Based on the current case data and fraud patterns, here's my analysis...\n\nKey points:\n• Risk factors indicate potential fraud\n• Similar patterns detected in 3 recent cases\n• Recommend escalation for further review`,
        timestamp: new Date().toISOString(),
        agent_name: 'Aegis AI Co-pilot',
        confidence: 0.92,
      }
      setMessages((prev) => [...prev, aiMessage])
      setIsLoading(false)
    }, 1500)
  }

  const handleClearChat = () => {
    setMessages([])
  }

  return (
    <MainLayout>
      <div className="h-[calc(100vh-4rem)] flex">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="border-b bg-background p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                <Brain className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold">AI Co-pilot</h1>
                <p className="text-sm text-muted-foreground">Your fraud analysis assistant</p>
              </div>
              <Badge variant="secondary" className="ml-2">
                <Sparkles className="h-3 w-3 mr-1" />
                Claude Sonnet 4
              </Badge>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={messages.length === 0}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearChat}
                disabled={messages.length === 0}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear
              </Button>
            </div>
          </div>

          {/* Messages */}
          <ScrollArea className="flex-1 p-6">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mb-6">
                  <Brain className="h-10 w-10 text-primary" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Welcome to AI Co-pilot</h2>
                <p className="text-muted-foreground mb-6 max-w-md">
                  Ask me anything about fraud cases, risk analysis, or fraud prevention strategies.
                  I'm here to help you make better decisions.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full">
                  {[
                    "Explain the risk factors in CASE-1234",
                    "What fraud typology is most common?",
                    "Show me cases with active call detected",
                    "How do I investigate mule networks?",
                  ].map((prompt, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      className="text-left justify-start h-auto py-3 px-4"
                      onClick={() => handleSendMessage(prompt)}
                    >
                      <Sparkles className="h-4 w-4 mr-2 flex-shrink-0" />
                      <span className="text-sm">{prompt}</span>
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-6 max-w-3xl mx-auto">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    <Avatar className="h-8 w-8 flex-shrink-0">
                      <AvatarFallback className={message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}>
                        {message.role === 'user' ? <User className="h-4 w-4" /> : <Brain className="h-4 w-4" />}
                      </AvatarFallback>
                    </Avatar>
                    <div className={`flex-1 space-y-2 ${message.role === 'user' ? 'items-end' : ''}`}>
                      <div
                        className={`rounded-lg p-4 ${
                          message.role === 'user'
                            ? 'bg-primary text-primary-foreground ml-12'
                            : 'bg-muted mr-12'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      </div>
                      <div className={`flex items-center gap-2 text-xs text-muted-foreground ${message.role === 'user' ? 'justify-end' : ''}`}>
                        <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                        {message.confidence && (
                          <Badge variant="outline" className="text-xs">
                            Confidence: {(message.confidence * 100).toFixed(0)}%
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-muted">
                        <Brain className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="rounded-lg p-4 bg-muted mr-12">
                        <div className="flex gap-1">
                          <div className="h-2 w-2 rounded-full bg-foreground/20 animate-pulse" />
                          <div className="h-2 w-2 rounded-full bg-foreground/20 animate-pulse delay-75" />
                          <div className="h-2 w-2 rounded-full bg-foreground/20 animate-pulse delay-150" />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>

          {/* Input */}
          <ChatInput onSend={handleSendMessage} disabled={isLoading} />
        </div>

        {/* Context Panel */}
        <div className="hidden lg:block w-96 border-l bg-muted/30">
          <ContextPanel />
        </div>
      </div>
    </MainLayout>
  )
}
