'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const mockData = [
  { range: '0-20', count: 850, color: 'hsl(142 76% 36%)' },
  { range: '20-40', count: 420, color: 'hsl(142 76% 36%)' },
  { range: '40-60', count: 280, color: 'hsl(38 92% 50%)' },
  { range: '60-80', count: 180, color: 'hsl(38 92% 50%)' },
  { range: '80-100', count: 95, color: 'hsl(0 84% 60%)' },
]

export function RiskDistributionChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Score Distribution</CardTitle>
        <CardDescription>Cases grouped by risk score ranges</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={mockData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis 
              dataKey="range" 
              className="text-xs"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <YAxis 
              className="text-xs"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
            />
            <Bar dataKey="count" radius={[8, 8, 0, 0]}>
              {mockData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="flex justify-center gap-4 mt-4">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-success" />
            <span className="text-xs text-muted-foreground">Low Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-warning" />
            <span className="text-xs text-muted-foreground">Medium Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-destructive" />
            <span className="text-xs text-muted-foreground">High Risk</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

