'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Loader2, AlertTriangle, CheckCircle, Clock, FileText, Shield, TrendingUp, User, ArrowLeft, Eye } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import Link from 'next/link'
import { PaginatedResponse } from '@/types'

interface AuditLog {
  log_id: string
  timestamp: string
  action: string
  entity_id: string
  entity_type: string
  user_id: string
  details: any
}

function getActivityIcon(action: string) {
  switch (action) {
    case 'INVESTIGATE':
      return <Shield className="h-5 w-5 text-blue-500" />
    case 'DECISION':
      return <CheckCircle className="h-5 w-5 text-green-500" />
    case 'ESCALATE':
      return <TrendingUp className="h-5 w-5 text-amber-500" />
    case 'ASSIGN':
      return <User className="h-5 w-5 text-purple-500" />
    case 'UPDATE':
      return <FileText className="h-5 w-5 text-slate-500" />
    case 'DIALOGUE':
      return <AlertTriangle className="h-5 w-5 text-red-500" />
    default:
      return <Clock className="h-5 w-5 text-slate-400" />
  }
}

export default function ActivityPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const response = await apiClient.getAuditLogs(1, 100)
        setLogs(response.items)
      } catch (e) {
        console.error("Failed to load audit logs", e)
      } finally {
        setIsLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/analyst">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Global Activity Feed</h1>
          <p className="text-muted-foreground mt-1">View all system events, agent decisions, and analyst actions across the AEGIS platform.</p>
        </div>
      </div>

      <Card className="border-2 shadow-sm">
        <CardHeader>
          <CardTitle>Audit Logs</CardTitle>
          <CardDescription>Chronological list of platform activity.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-64 border rounded-xl bg-muted/20">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-4">
              {logs.map((log) => (
                <div key={log.log_id} className="flex items-start gap-4 p-5 rounded-xl bg-muted/40 border transition-all hover:bg-muted/60 hover:shadow-sm">
                  <div className="mt-1 flex-shrink-0 bg-background p-2.5 rounded-full border shadow-sm">
                    {getActivityIcon(log.action)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-semibold text-base truncate">
                        {log.action} {log.entity_type ? log.entity_type.toUpperCase() : ''}
                      </p>
                      <span className="text-xs text-muted-foreground flex-shrink-0 bg-background px-2 py-1 rounded-md border">
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="text-sm text-foreground/80 mt-1.5 flex items-center gap-2 flex-wrap">
                      <Badge variant="outline" className="font-mono bg-background">{log.user_id}</Badge>
                      <span className="text-muted-foreground">→</span>
                      <span className="font-medium text-muted-foreground">Entity:</span> 
                      <code className="bg-background px-1.5 py-0.5 rounded border text-xs">{log.entity_id}</code>
                    </div>
                    {log.details && Object.keys(log.details).length > 0 && (
                        <div className="text-sm text-muted-foreground mt-3 bg-background p-3 rounded-lg border text-xs font-mono break-all whitespace-pre-wrap">
                            {JSON.stringify(log.details, null, 2)}
                        </div>
                    )}
                  </div>
                  {log.entity_type === 'case' && (
                    <div className="flex-shrink-0">
                        <Link href={`/analyst/cases/${log.entity_id}`}>
                            <Button variant="outline" size="sm" className="hidden sm:flex shadow-sm" title="View associated case">
                                <Eye className="h-4 w-4 mr-2" />
                                View Case
                            </Button>
                            <Button variant="outline" size="icon" className="sm:hidden shadow-sm" title="View associated case">
                                <Eye className="h-4 w-4" />
                            </Button>
                        </Link>
                    </div>
                  )}
                </div>
              ))}
              
              {logs.length === 0 && (
                <div className="text-center py-16 px-4 bg-muted/20 rounded-xl border border-dashed text-muted-foreground">
                  No activity logs found. Try processing some cases to populate the system truth state.
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
