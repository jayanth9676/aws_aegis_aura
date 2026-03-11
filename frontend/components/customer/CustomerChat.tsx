'use client'

import { useState } from 'react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Shield, User, AlertTriangle } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { AgentMessage } from '@/types'

interface CustomerChatProps {
  messages: AgentMessage[]
  streamingMessage?: string | null
  onResponse: (response: string) => void
}

export function CustomerChat({ messages, streamingMessage, onResponse }: CustomerChatProps) {
  const [selectedResponse, setSelectedResponse] = useState<string | null>(null)

  const latestMessage = messages[messages.length - 1]
  const suggestions = latestMessage?.suggestions || []

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 p-6">
        <div className="space-y-6 max-w-3xl mx-auto">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <Avatar className="h-10 w-10 flex-shrink-0">
                <AvatarFallback
                  className={message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}
                >
                  {message.role === 'user' ? (
                    <User className="h-5 w-5" />
                  ) : (
                    <Shield className="h-5 w-5" />
                  )}
                </AvatarFallback>
              </Avatar>

              <div className={`flex-1 ${message.role === 'user' ? 'items-end' : ''}`}>
                <div
                  className={`rounded-2xl p-6 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground ml-12'
                      : 'bg-card border-2 mr-12'
                  }`}
                >
                  {message.role === 'assistant' && message.content.includes('⚠️') && (
                    <div className="flex items-center gap-2 mb-3 pb-3 border-b border-border/50">
                      <AlertTriangle className="h-5 w-5 text-warning" />
                      <span className="font-semibold text-warning">Security Warning</span>
                    </div>
                  )}
                  <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-2 px-2">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {/* Streaming Indicator Message */}
          {streamingMessage && (
            <div className="flex gap-4">
              <Avatar className="h-10 w-10 flex-shrink-0">
                <AvatarFallback className="bg-muted">
                  <Shield className="h-5 w-5" />
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="rounded-2xl p-6 bg-card border-2 mr-12">
                  <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {streamingMessage}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Response Options */}
      {suggestions.length > 0 && (
        <div className="border-t bg-background p-6">
          <p className="text-sm font-medium mb-4">Please choose an option:</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl mx-auto">
            {suggestions.map((suggestion, index) => (
              <Button
                key={index}
                variant={selectedResponse === suggestion ? 'default' : 'outline'}
                className="h-auto py-4 text-left justify-start whitespace-normal"
                onClick={() => {
                  setSelectedResponse(suggestion)
                  onResponse(suggestion)
                }}
              >
                {suggestion}
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

