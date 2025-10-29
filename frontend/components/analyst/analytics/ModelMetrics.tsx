'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { TrendingUp, Calendar, Cpu } from 'lucide-react'

const metrics = [
  { name: 'AUC Score', value: 0.962, target: 0.95, color: 'text-success' },
  { name: 'Precision', value: 0.94, target: 0.90, color: 'text-success' },
  { name: 'Recall', value: 0.91, target: 0.88, color: 'text-success' },
  { name: 'F1 Score', value: 0.925, target: 0.90, color: 'text-success' },
]

export function ModelMetrics() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>ML Model Performance</CardTitle>
            <CardDescription>Current fraud detection model metrics</CardDescription>
          </div>
          <Badge variant="outline" className="gap-2">
            <Cpu className="h-3 w-3" />
            v2.3.1
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4">
          {metrics.map((metric) => (
            <div key={metric.name} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{metric.name}</span>
                <span className={`text-2xl font-bold ${metric.color}`}>
                  {metric.value.toFixed(3)}
                </span>
              </div>
              <Progress 
                value={metric.value * 100} 
                className="h-2"
                indicatorClassName="bg-success"
              />
              <p className="text-xs text-muted-foreground">
                Target: {metric.target.toFixed(2)} {metric.value >= metric.target && '✓'}
              </p>
            </div>
          ))}
        </div>

        {/* Model Info */}
        <div className="space-y-3 pt-4 border-t">
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Last Trained:</span>
            <span className="font-medium">January 15, 2025</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Training Samples:</span>
            <span className="font-medium">1,250,000</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Model Type:</span>
            <span className="font-medium">XGBoost + LightGBM + CatBoost Ensemble</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

