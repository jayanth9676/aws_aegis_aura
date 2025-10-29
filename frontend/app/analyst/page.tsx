'use client'

import { MainLayout } from '@/components/layout/MainLayout'
import { EnhancedDashboard } from '@/components/analyst/EnhancedDashboard'
import { PerformanceMetrics } from '@/components/analyst/PerformanceMetrics'
import { QuickActions } from '@/components/analyst/QuickActions'
import { ActivityFeed } from '@/components/analyst/ActivityFeed'
import { EnhancedCaseList } from '@/components/analyst/EnhancedCaseList'

export default function AnalystDashboard() {
  return (
    <MainLayout>
      <div className="p-6 space-y-6">
        {/* Dashboard Statistics */}
        <EnhancedDashboard />

        {/* Performance Metrics */}
        <PerformanceMetrics />

        {/* Quick Actions and Activity Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <QuickActions />
          </div>
          <div className="lg:col-span-1">
            <ActivityFeed />
          </div>
        </div>

        {/* Recent Cases */}
        <EnhancedCaseList />
      </div>
    </MainLayout>
  )
}
