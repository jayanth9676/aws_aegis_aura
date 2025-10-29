'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { AlertTriangle, TrendingUp, Network, Brain, Shield } from 'lucide-react'
import type { Case } from '@/types'
import { cn } from '@/lib/utils'

interface RiskAssessmentProps {
  caseData: Case
}

interface RiskFactor {
  name: string
  score: number
  description: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
}

// Mock risk factors - in production these would come from the case data
function extractRiskFactors(caseData: Case): RiskFactor[] {
  const factors: RiskFactor[] = []

  // Add factors based on case evidence
  caseData.evidence?.forEach((evidence) => {
    factors.push({
      name: evidence.type,
      score: evidence.severity === 'HIGH' ? 85 : evidence.severity === 'MEDIUM' ? 60 : 35,
      description: evidence.description,
      severity: evidence.severity,
    })
  })

  // If no evidence, show common factors
  if (factors.length === 0) {
    factors.push(
      {
        name: 'New Payee',
        score: 75,
        description: 'First time payment to this payee',
        severity: 'HIGH',
      },
      {
        name: 'High Amount',
        score: 65,
        description: 'Transaction amount exceeds normal patterns',
        severity: 'MEDIUM',
      },
      {
        name: 'Active Call Detected',
        score: 90,
        description: 'Customer was on a phone call during transaction',
        severity: 'HIGH',
      }
    )
  }

  return factors.sort((a, b) => b.score - a.score).slice(0, 5)
}

function getSeverityColor(severity: string) {
  switch (severity) {
    case 'HIGH':
      return 'bg-destructive'
    case 'MEDIUM':
      return 'bg-warning'
    case 'LOW':
      return 'bg-success'
    default:
      return 'bg-muted'
  }
}

export function RiskAssessment({ caseData }: RiskAssessmentProps) {
  const riskFactors = extractRiskFactors(caseData)
  const riskScore = caseData.risk_score || 0
  const confidence = caseData.confidence || 0

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          <div>
            <CardTitle>Risk Assessment</CardTitle>
            <CardDescription>ML-powered fraud detection analysis</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Score */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Overall Risk Score</p>
              <p className="text-xs text-muted-foreground">
                Confidence: {(confidence * 100).toFixed(1)}%
              </p>
            </div>
            <div className={cn(
              'text-3xl font-bold',
              riskScore >= 85 ? 'text-destructive' :
              riskScore >= 60 ? 'text-warning' :
              'text-success'
            )}>
              {riskScore}
            </div>
          </div>
          <Progress 
            value={riskScore} 
            className="h-3"
            indicatorClassName={
              riskScore >= 85 ? 'bg-destructive' :
              riskScore >= 60 ? 'bg-warning' : 
              'bg-success'
            }
          />
        </div>

        {/* Risk Factor Breakdown */}
        <div className="space-y-3 pt-4 border-t">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            <p className="text-sm font-medium">Risk Factors</p>
          </div>
          <div className="space-y-3">
            {riskFactors.map((factor, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-start justify-between">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant={
                          factor.severity === 'HIGH' ? 'destructive' :
                          factor.severity === 'MEDIUM' ? 'default' :
                          'secondary'
                        }
                        className="text-xs"
                      >
                        {factor.name}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        Score: {factor.score}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground pl-1">
                      {factor.description}
                    </p>
                  </div>
                </div>
                <div className="relative">
                  <Progress 
                    value={factor.score} 
                    className="h-1.5"
                    indicatorClassName={getSeverityColor(factor.severity)}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ML Model Info */}
        <div className="space-y-3 pt-4 border-t">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-muted-foreground" />
            <p className="text-sm font-medium">ML Model Prediction</p>
          </div>
          <div className="grid grid-cols-2 gap-4 pl-6">
            <div>
              <p className="text-xs text-muted-foreground">Fraud Probability</p>
              <p className="text-sm font-bold text-destructive">
                {(riskScore / 100).toFixed(3)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Model Confidence</p>
              <p className="text-sm font-bold">
                {(confidence * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        {/* Fraud Typology */}
        {caseData.fraud_typology && (
          <div className="space-y-3 pt-4 border-t">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <p className="text-sm font-medium">Fraud Typology Match</p>
            </div>
            <div className="pl-6">
              <Badge variant="outline" className="text-sm">
                {caseData.fraud_typology}
              </Badge>
            </div>
          </div>
        )}

        {/* Network Analysis */}
        {caseData.network_data && caseData.network_data.length > 0 && (
          <div className="space-y-3 pt-4 border-t">
            <div className="flex items-center gap-2">
              <Network className="h-4 w-4 text-muted-foreground" />
              <p className="text-sm font-medium">Network Analysis</p>
            </div>
            <div className="grid grid-cols-2 gap-4 pl-6">
              <div>
                <p className="text-xs text-muted-foreground">Connected Entities</p>
                <p className="text-sm font-bold">
                  {caseData.network_data.length}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Mule Accounts</p>
                <p className="text-sm font-bold text-destructive">
                  {caseData.network_data.filter(n => n.type === 'MULE').length}
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

