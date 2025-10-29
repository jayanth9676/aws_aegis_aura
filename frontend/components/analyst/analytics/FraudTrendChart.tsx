'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const mockData = [
  { date: 'Jan 10', fraudCount: 12, totalTransactions: 1250, fraudRate: 0.96 },
  { date: 'Jan 11', fraudCount: 18, totalTransactions: 1320, fraudRate: 1.36 },
  { date: 'Jan 12', fraudCount: 15, totalTransactions: 1180, fraudRate: 1.27 },
  { date: 'Jan 13', fraudCount: 22, totalTransactions: 1420, fraudRate: 1.55 },
  { date: 'Jan 14', fraudCount: 19, totalTransactions: 1390, fraudRate: 1.37 },
  { date: 'Jan 15', fraudCount: 25, totalTransactions: 1510, fraudRate: 1.66 },
  { date: 'Jan 16', fraudCount: 20, totalTransactions: 1280, fraudRate: 1.56 },
  { date: 'Jan 17', fraudCount: 16, totalTransactions: 1190, fraudRate: 1.34 },
]

export function FraudTrendChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Fraud Detection Trends</CardTitle>
        <CardDescription>Daily fraud cases vs total transactions (Last 7 days)</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={mockData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis 
              dataKey="date" 
              className="text-xs"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <YAxis 
              yAxisId="left"
              className="text-xs"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <YAxis 
              yAxisId="right" 
              orientation="right"
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
            <Legend />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="fraudCount" 
              stroke="hsl(var(--destructive))" 
              strokeWidth={2}
              name="Fraud Cases"
            />
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="totalTransactions" 
              stroke="hsl(var(--primary))" 
              strokeWidth={2}
              name="Total Transactions"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

