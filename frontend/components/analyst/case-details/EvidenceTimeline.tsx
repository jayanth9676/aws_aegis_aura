'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Shield,
  User,
  Activity,
  Brain,
} from 'lucide-react'
import type { TimelineEvent } from '@/types'
import { cn } from '@/lib/utils'

interface EvidenceTimelineProps {
  events: TimelineEvent[]
}

function getEventIcon(type: TimelineEvent['type']) {
  switch (type) {
    case 'TRANSACTION':
      return <Activity className="h-4 w-4" />
    case 'AGENT_ANALYSIS':
      return <Brain className="h-4 w-4" />
    case 'ANALYST_ACTION':
      return <User className="h-4 w-4" />
    case 'CUSTOMER_RESPONSE':
      return <FileText className="h-4 w-4" />
    case 'SYSTEM_DECISION':
      return <Shield className="h-4 w-4" />
    default:
      return <Clock className="h-4 w-4" />
  }
}

function getEventColor(type: TimelineEvent['type']) {
  switch (type) {
    case 'TRANSACTION':
      return 'text-blue-600 bg-blue-100'
    case 'AGENT_ANALYSIS':
      return 'text-purple-600 bg-purple-100'
    case 'ANALYST_ACTION':
      return 'text-green-600 bg-green-100'
    case 'CUSTOMER_RESPONSE':
      return 'text-orange-600 bg-orange-100'
    case 'SYSTEM_DECISION':
      return 'text-red-600 bg-red-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

function getTimeAgo(timestamp: string): string {
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  const diff = now - then

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

export function EvidenceTimeline({ events }: EvidenceTimelineProps) {
  // Sort events by timestamp (newest first)
  const sortedEvents = [...events].sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary" />
          <div>
            <CardTitle>Evidence Timeline</CardTitle>
            <CardDescription>Chronological event history</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px] pr-4">
          <div className="relative space-y-4">
            {/* Timeline Line */}
            <div className="absolute left-[15px] top-2 bottom-2 w-px bg-border" />

            {/* Events */}
            {sortedEvents.map((event, index) => (
              <div key={event.id} className="relative flex gap-4 pb-4">
                {/* Icon */}
                <div className={cn(
                  'relative z-10 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full',
                  getEventColor(event.type)
                )}>
                  {getEventIcon(event.type)}
                </div>

                {/* Content */}
                <div className="flex-1 space-y-2 pt-0.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="text-sm font-medium leading-none">
                        {event.description}
                      </p>
                      {event.agent && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Agent: {event.agent}
                        </p>
                      )}
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-xs text-muted-foreground">
                        {getTimeAgo(event.timestamp)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(event.timestamp).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                  </div>

                  {/* Risk Impact */}
                  {event.risk_impact !== undefined && (
                    <Badge 
                      variant={
                        event.risk_impact >= 20 ? 'destructive' :
                        event.risk_impact >= 10 ? 'default' :
                        'secondary'
                      }
                      className="text-xs"
                    >
                      Risk Impact: +{event.risk_impact}
                    </Badge>
                  )}

                  {/* Additional Data */}
                  {event.data && Object.keys(event.data).length > 0 && (
                    <details className="group">
                      <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground list-none">
                        <span className="inline-flex items-center gap-1">
                          <span className="group-open:rotate-90 transition-transform inline-block">
                            ▶
                          </span>
                          View details
                        </span>
                      </summary>
                      <div className="mt-2 rounded-md bg-muted p-3 text-xs">
                        <pre className="overflow-auto text-xs">
                          {JSON.stringify(event.data, null, 2)}
                        </pre>
                      </div>
                    </details>
                  )}
                </div>
              </div>
            ))}

            {/* Empty State */}
            {sortedEvents.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Clock className="h-12 w-12 text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground">No timeline events recorded yet</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

