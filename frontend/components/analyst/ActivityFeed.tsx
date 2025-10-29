'use client'

import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Shield,
  TrendingUp,
  User,
  ArrowRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface Activity {
  id: string
  type: 'CASE_CREATED' | 'CASE_RESOLVED' | 'CASE_ESCALATED' | 'HIGH_RISK_DETECTED' | 'MODEL_UPDATED' | 'ANALYST_ACTION'
  title: string
  description: string
  timestamp: string
  caseId?: string
  severity?: 'LOW' | 'MEDIUM' | 'HIGH'
}

// Mock activity data - in production this would come from WebSocket/API
const mockActivities: Activity[] = [
  {
    id: '1',
    type: 'HIGH_RISK_DETECTED',
    title: 'High Risk Transaction Detected',
    description: 'Case #CASE-1245 flagged with risk score 94. Active call detected.',
    timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    caseId: 'CASE-1245',
    severity: 'HIGH',
  },
  {
    id: '2',
    type: 'CASE_RESOLVED',
    title: 'Case Resolved',
    description: 'Case #CASE-1240 resolved by analyst. Payment approved after verification.',
    timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    caseId: 'CASE-1240',
    severity: 'LOW',
  },
  {
    id: '3',
    type: 'CASE_ESCALATED',
    title: 'Case Escalated',
    description: 'Case #CASE-1238 escalated to senior analyst. Complex mule network detected.',
    timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    caseId: 'CASE-1238',
    severity: 'HIGH',
  },
  {
    id: '4',
    type: 'MODEL_UPDATED',
    title: 'ML Model Updated',
    description: 'Fraud detection model v2.3.1 deployed. Improved AUC: 0.96.',
    timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    severity: 'MEDIUM',
  },
  {
    id: '5',
    type: 'CASE_CREATED',
    title: 'New Case Created',
    description: 'Case #CASE-1244 auto-created. Payee verification mismatch.',
    timestamp: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
    caseId: 'CASE-1244',
    severity: 'MEDIUM',
  },
]

function getActivityIcon(type: Activity['type']) {
  switch (type) {
    case 'HIGH_RISK_DETECTED':
      return <AlertTriangle className="h-5 w-5 text-destructive" />
    case 'CASE_RESOLVED':
      return <CheckCircle className="h-5 w-5 text-success" />
    case 'CASE_ESCALATED':
      return <TrendingUp className="h-5 w-5 text-warning" />
    case 'MODEL_UPDATED':
      return <Shield className="h-5 w-5 text-info" />
    case 'CASE_CREATED':
      return <FileText className="h-5 w-5 text-primary" />
    case 'ANALYST_ACTION':
      return <User className="h-5 w-5 text-muted-foreground" />
    default:
      return <Clock className="h-5 w-5 text-muted-foreground" />
  }
}

function getSeverityBadge(severity?: Activity['severity']) {
  if (!severity) return null

  const variants = {
    LOW: 'default',
    MEDIUM: 'secondary',
    HIGH: 'destructive',
  } as const

  return (
    <Badge variant={variants[severity]} className="text-xs">
      {severity}
    </Badge>
  )
}

function getTimeAgo(timestamp: string): string {
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  const diff = now - then

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)

  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  return `${hours}h ago`
}

export function ActivityFeed() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Live system events and updates</CardDescription>
          </div>
          <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-4">
            {mockActivities.map((activity, index) => (
              <div
                key={activity.id}
                className={cn(
                  'flex gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer',
                  index === 0 && 'bg-muted/30'
                )}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getActivityIcon(activity.type)}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium leading-none">{activity.title}</p>
                    {getSeverityBadge(activity.severity)}
                  </div>
                  <p className="text-sm text-muted-foreground">{activity.description}</p>
                  <div className="flex items-center gap-2">
                    <p className="text-xs text-muted-foreground">
                      {getTimeAgo(activity.timestamp)}
                    </p>
                    {activity.caseId && (
                      <Link
                        href={`/analyst/cases/${activity.caseId}`}
                        className="text-xs text-primary hover:underline flex items-center gap-1"
                        onClick={(e) => e.stopPropagation()}
                      >
                        View case
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        <div className="mt-4 pt-4 border-t">
          <Link href="/analyst/activity">
            <Button variant="outline" size="sm" className="w-full">
              View All Activity
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}

