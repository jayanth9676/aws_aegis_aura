'use client'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Copy, ThumbsUp, ThumbsDown, User, Bot } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { AgentMessage } from '@/types'

interface ChatMessageProps {
  message: AgentMessage
}

export function ChatMessage({ message }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={cn('flex gap-3 mb-4', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <Avatar className="h-8 w-8 flex-shrink-0">
        <AvatarFallback className={isUser ? 'bg-primary text-primary-foreground' : 'bg-secondary'}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      {/* Message Content */}
      <div className={cn('flex-1 space-y-2', isUser && 'flex flex-col items-end')}>
        {/* Header */}
        <div className={cn('flex items-center gap-2 text-sm', isUser && 'flex-row-reverse')}>
          <span className="font-medium">{isUser ? 'You' : message.agent_name || 'AI Co-pilot'}</span>
          <span className="text-xs text-muted-foreground">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          {message.confidence && (
            <span className="text-xs text-muted-foreground">
              Confidence: {(message.confidence * 100).toFixed(0)}%
            </span>
          )}
        </div>

        {/* Message Bubble */}
        <div
          className={cn(
            'rounded-lg p-4 max-w-3xl',
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted'
          )}
        >
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {message.content.split('\n').map((line, i) => (
              <p key={i} className={cn('mb-2 last:mb-0', isUser && 'text-primary-foreground')}>
                {line}
              </p>
            ))}
          </div>

          {/* Suggestions */}
          {message.suggestions && message.suggestions.length > 0 && (
            <div className="mt-3 pt-3 border-t space-y-2">
              <p className="text-xs font-medium">Suggested follow-ups:</p>
              <div className="flex flex-wrap gap-2">
                {message.suggestions.map((suggestion, i) => (
                  <Button
                    key={i}
                    variant="outline"
                    size="sm"
                    className="text-xs h-7"
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        {!isUser && (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-7 text-xs"
            >
              <Copy className="h-3 w-3 mr-1" />
              {copied ? 'Copied!' : 'Copy'}
            </Button>
            <Button variant="ghost" size="sm" className="h-7">
              <ThumbsUp className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="sm" className="h-7">
              <ThumbsDown className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

