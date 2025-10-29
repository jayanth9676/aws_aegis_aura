'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { SHAPExplanation } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface SHAPChartProps {
  data: SHAPExplanation
}

export function SHAPChart({ data }: SHAPChartProps) {
  // Sort by absolute SHAP value and take top 10
  const chartData = [...data.shap_values]
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .slice(0, 10)
    .map((item) => ({
      feature: item.feature_name,
      value: item.shap_value,
      featureValue: item.feature_value,
      color: item.shap_value > 0 ? '#ef4444' : '#10b981',
    }))

  return (
    <div className="space-y-4">
      {/* Header Info */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Model: {data.model_name}</p>
          <p className="text-sm text-muted-foreground">Version: {data.model_version}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-muted-foreground">Base Value</p>
          <p className="text-2xl font-bold">{data.base_value.toFixed(3)}</p>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis
            type="number"
            className="text-xs"
            tick={{ fill: 'hsl(var(--muted-foreground))' }}
          />
          <YAxis
            type="category"
            dataKey="feature"
            className="text-xs"
            tick={{ fill: 'hsl(var(--muted-foreground))' }}
            width={140}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload[0]) {
                const data = payload[0].payload
                return (
                  <div className="bg-background border rounded-lg p-3 shadow-lg">
                    <p className="font-semibold mb-1">{data.feature}</p>
                    <p className="text-sm text-muted-foreground mb-1">
                      Value: {String(data.featureValue)}
                    </p>
                    <p className="text-sm">
                      SHAP Impact: {data.value > 0 ? '+' : ''}
                      {data.value.toFixed(4)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {data.value > 0 ? 'Increases fraud risk' : 'Decreases fraud risk'}
                    </p>
                  </div>
                )
              }
              return null
            }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 pt-4 border-t">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-destructive" />
          <span className="text-sm text-muted-foreground">Increases Risk (Positive SHAP)</span>
        </div>
        <div className="flex items-center gap-2">
          <TrendingDown className="h-4 w-4 text-success" />
          <span className="text-sm text-muted-foreground">Decreases Risk (Negative SHAP)</span>
        </div>
      </div>

      {/* Top Features Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-4">
        {chartData.slice(0, 4).map((item, index) => (
          <div key={index} className="p-3 border rounded-lg">
            <div className="flex items-start justify-between mb-1">
              <p className="text-sm font-medium">{item.feature}</p>
              <Badge variant={item.value > 0 ? 'destructive' : 'outline'}>
                #{index + 1}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mb-1">
              Value: {String(item.featureValue)}
            </p>
            <p className={`text-sm font-bold ${item.value > 0 ? 'text-destructive' : 'text-success'}`}>
              {item.value > 0 ? '+' : ''}{item.value.toFixed(4)}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
