'use client'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertTriangle,
  MoreVertical,
  User,
} from 'lucide-react'
import Link from 'next/link'
import type { Case } from '@/types'
import { cn } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface CaseHeaderProps {
  caseData: Case
  onApprove?: () => void
  onBlock?: () => void
  onEscalate?: () => void
  onClose?: () => void
}

function getRiskColor(score: number) {
  if (score >= 85) return 'text-destructive'
  if (score >= 60) return 'text-warning'
  return 'text-success'
}

function getRiskBgColor(score: number) {
  if (score >= 85) return 'bg-destructive/10'
  if (score >= 60) return 'bg-warning/10'
  return 'bg-success/10'
}

function getStatusBadgeVariant(status: string) {
  switch (status) {
    case 'NEW':
      return 'default'
    case 'INVESTIGATING':
      return 'secondary'
    case 'ESCALATED':
      return 'destructive'
    case 'RESOLVED':
    case 'CLOSED':
      return 'outline'
    default:
      return 'secondary'
  }
}

export function CaseHeader({
  caseData,
  onApprove,
  onBlock,
  onEscalate,
  onClose,
}: CaseHeaderProps) {
  const riskScore = caseData.risk_score || 0
  const confidence = caseData.confidence || 0

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link href="/analyst/cases">
        <Button variant="ghost" size="sm">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Cases
        </Button>
      </Link>

      {/* Main Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        {/* Left Side - Case Info */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold">{caseData.case_id}</h1>
            <Badge variant={getStatusBadgeVariant(caseData.status) as any} className="text-sm">
              {caseData.status.replace(/_/g, ' ')}
            </Badge>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <span>Created:</span>
              <span className="font-medium text-foreground">
                {new Date(caseData.created_at).toLocaleString()}
              </span>
            </div>
            {caseData.assigned_analyst && (
              <div className="flex items-center gap-2">
                <Avatar className="h-6 w-6">
                  <AvatarFallback className="text-xs">
                    {caseData.assigned_analyst.substring(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <span>Assigned to:</span>
                <span className="font-medium text-foreground">{caseData.assigned_analyst}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Side - Risk Score & Actions */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
          {/* Risk Score Gauge */}
          <div className={cn('flex flex-col items-center justify-center p-6 rounded-lg border-2', getRiskBgColor(riskScore))}>
            <div className="text-center space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Risk Score
              </p>
              <div className={cn('text-4xl font-bold', getRiskColor(riskScore))}>
                {riskScore}
              </div>
              <div className="w-full">
                <Progress 
                  value={riskScore} 
                  className="h-2 w-32"
                  indicatorClassName={
                    riskScore >= 85 ? 'bg-destructive' :
                    riskScore >= 60 ? 'bg-warning' : 
                    'bg-success'
                  }
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Confidence: {(confidence * 100).toFixed(1)}%
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex sm:flex-col gap-2">
            {caseData.status === 'NEW' || caseData.status === 'INVESTIGATING' ? (
              <>
                <Button onClick={onApprove} variant="default" className="flex-1 sm:flex-none">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Approve
                </Button>
                <Button onClick={onBlock} variant="destructive" className="flex-1 sm:flex-none">
                  <XCircle className="h-4 w-4 mr-2" />
                  Block
                </Button>
                <Button onClick={onEscalate} variant="outline" className="flex-1 sm:flex-none">
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Escalate
                </Button>
              </>
            ) : (
              <Button onClick={onClose} variant="outline" disabled={caseData.status === 'CLOSED'}>
                Close Case
              </Button>
            )}

            {/* More Actions Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <User className="h-4 w-4 mr-2" />
                  Reassign
                </DropdownMenuItem>
                <DropdownMenuItem>Export Report</DropdownMenuItem>
                <DropdownMenuItem>View History</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </div>
  )
}

