'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MetricData {
  label: string
  value: number
  target: number
  unit: string
  trend?: {
    value: number
    isPositive: boolean
  }
  description: string
}

const metrics: MetricData[] = [
  {
    label: 'Avg Risk Score',
    value: 42.5,
    target: 50,
    unit: '',
    description: 'Lower is better',
    trend: {
      value: 5.2,
      isPositive: true,
    },
  },
  {
    label: 'Fraud Detection Rate',
    value: 96.2,
    target: 95,
    unit: '%',
    description: 'Target: >95%',
    trend: {
      value: 1.2,
      isPositive: true,
    },
  },
  {
    label: 'False Positive Rate',
    value: 2.1,
    target: 3,
    unit: '%',
    description: 'Target: <3%',
    trend: {
      value: 0.3,
      isPositive: true,
    },
  },
]

function getProgressColor(value: number, target: number, lowerIsBetter: boolean = false): string {
  const percentage = lowerIsBetter ? (target - value) / target : value / target
  
  if (percentage >= 1) return 'bg-success'
  if (percentage >= 0.8) return 'bg-primary'
  if (percentage >= 0.6) return 'bg-warning'
  return 'bg-destructive'
}

export function PerformanceMetrics() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {metrics.map((metric, index) => {
        const lowerIsBetter = metric.label.includes('Risk Score') || metric.label.includes('False Positive')
        const progressValue = lowerIsBetter 
          ? ((metric.target - metric.value) / metric.target) * 100
          : (metric.value / metric.target) * 100
        
        const progressColor = getProgressColor(metric.value, metric.target, lowerIsBetter)

        return (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium">{metric.label}</CardTitle>
              <CardDescription>{metric.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-baseline space-x-2">
                <span className="text-3xl font-bold text-foreground">
                  {metric.value}
                </span>
                <span className="text-sm text-muted-foreground">{metric.unit}</span>
                {metric.trend && (
                  <div
                    className={cn(
                      'flex items-center text-xs font-medium ml-auto',
                      metric.trend.isPositive ? 'text-success' : 'text-destructive'
                    )}
                  >
                    {metric.trend.isPositive ? (
                      <TrendingUp className="h-3 w-3 mr-1" />
                    ) : (
                      <TrendingDown className="h-3 w-3 mr-1" />
                    )}
                    {metric.trend.value}%
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Progress to target</span>
                  <span>{Math.min(progressValue, 100).toFixed(0)}%</span>
                </div>
                <Progress 
                  value={Math.min(progressValue, 100)} 
                  className="h-2"
                  indicatorClassName={progressColor}
                />
              </div>

              <div className="text-xs text-muted-foreground">
                Target: {lowerIsBetter ? '<' : '>'} {metric.target}{metric.unit}
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

