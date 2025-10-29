'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

const mockData = [
  { name: 'Investment Scam', value: 35, color: '#ef4444' },
  { name: 'Romance Scam', value: 28, color: '#f97316' },
  { name: 'Invoice Fraud', value: 20, color: '#eab308' },
  { name: 'Impersonation', value: 12, color: '#3b82f6' },
  { name: 'Other', value: 5, color: '#8b5cf6' },
]

export function FraudTypologyChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Fraud Typology Breakdown</CardTitle>
        <CardDescription>Distribution by fraud type</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={mockData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {mockData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
            />
            <Legend 
              verticalAlign="bottom" 
              height={36}
              formatter={(value, entry: any) => `${value} (${entry.payload.value}%)`}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

