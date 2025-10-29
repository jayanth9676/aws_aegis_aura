'use client'

import { MainLayout } from '@/components/layout/MainLayout'
import { FraudTrendChart } from '@/components/analyst/analytics/FraudTrendChart'
import { RiskDistributionChart } from '@/components/analyst/analytics/RiskDistributionChart'
import { FraudTypologyChart } from '@/components/analyst/analytics/FraudTypologyChart'
import { ModelMetrics } from '@/components/analyst/analytics/ModelMetrics'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { RefreshCw, Download, Calendar } from 'lucide-react'

export default function AnalyticsDashboard() {
  return (
    <MainLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Fraud trends and model performance metrics
            </p>
          </div>
          <div className="flex gap-2">
            <Select defaultValue="7days">
              <SelectTrigger className="w-40">
                <Calendar className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7days">Last 7 days</SelectItem>
                <SelectItem value="30days">Last 30 days</SelectItem>
                <SelectItem value="90days">Last 90 days</SelectItem>
                <SelectItem value="custom">Custom range</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="icon">
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="lg:col-span-2">
            <FraudTrendChart />
          </div>
          <RiskDistributionChart />
          <FraudTypologyChart />
          <div className="lg:col-span-2">
            <ModelMetrics />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
