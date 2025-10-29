'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '@/lib/api-client'
import { AlertTriangle, TrendingUp, CheckCircle, Clock } from 'lucide-react'

interface DashboardStats {
  active_cases: number
  high_risk_cases: number
  resolved_today: number
  total_cases: number
  avg_risk_score: number
  fraud_detection_rate: number
  false_positive_rate: number
}

export function EnhancedDashboard() {
  // Fetch dashboard stats with auto-refresh
  const { data: stats, isLoading, error } = useQuery<DashboardStats>({
    queryKey: ['dashboardStats'],
    queryFn: () => apiClient.getDashboardStats(),
    refetchInterval: 10000, // Refresh every 10 seconds
    refetchOnWindowFocus: true,
  })

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-gray-200 rounded w-24"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded w-16"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <p className="font-semibold text-yellow-900">AWS Not Configured</p>
                <p className="text-yellow-700 text-sm mt-1">
                  DynamoDB tables not found. Please run the setup scripts:
                </p>
                <ol className="text-yellow-700 text-sm mt-2 ml-4 space-y-1 list-decimal">
                  <li><code className="bg-yellow-100 px-1 rounded">bash infrastructure/scripts/setup_aws_infrastructure.sh</code></li>
                  <li><code className="bg-yellow-100 px-1 rounded">python infrastructure/scripts/fetch_aws_resources.py</code></li>
                  <li><code className="bg-yellow-100 px-1 rounded">python datasets/aegis_datasets/populate_aws.py</code></li>
                </ol>
                <p className="text-yellow-700 text-sm mt-2">
                  See <code className="bg-yellow-100 px-1 rounded">START_HERE.md</code> for detailed instructions.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Fraud Analysis Dashboard</h1>
          <p className="text-gray-500 mt-1">Real-time fraud detection monitoring</p>
        </div>
        <Badge variant="success" className="text-sm">
          Live
        </Badge>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Active Cases */}
        <StatCard
          title="Active Cases"
          value={stats?.active_cases || 0}
          icon={<Clock className="h-5 w-5" />}
          description="Currently under investigation"
          trend={null}
          variant="default"
        />

        {/* High Risk Cases */}
        <StatCard
          title="High Risk Cases"
          value={stats?.high_risk_cases || 0}
          icon={<AlertTriangle className="h-5 w-5" />}
          description="Require immediate attention"
          trend={null}
          variant="warning"
        />

        {/* Resolved Today */}
        <StatCard
          title="Resolved Today"
          value={stats?.resolved_today || 0}
          icon={<CheckCircle className="h-5 w-5" />}
          description="Cases closed today"
          trend={null}
          variant="success"
        />

        {/* Total Cases */}
        <StatCard
          title="Total Cases"
          value={stats?.total_cases || 0}
          icon={<TrendingUp className="h-5 w-5" />}
          description="All time case count"
          trend={null}
          variant="default"
        />
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-medium">Average Risk Score</CardTitle>
            <CardDescription>Across all transactions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {stats?.avg_risk_score.toFixed(1) || '0.0'}
            </div>
            <div className="mt-2">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min((stats?.avg_risk_score || 0) / 100 * 100, 100)}%` }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base font-medium">Fraud Detection Rate</CardTitle>
            <CardDescription>Successful fraud identification</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {stats?.fraud_detection_rate.toFixed(1) || '0.0'}%
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Target: {'>'} 95%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base font-medium">False Positive Rate</CardTitle>
            <CardDescription>Legitimate transactions flagged</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {stats?.false_positive_rate.toFixed(1) || '0.0'}%
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Target: {'<'} 3%
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  description: string
  trend: { value: number; isPositive: boolean } | null
  variant: 'default' | 'success' | 'warning' | 'destructive'
}

function StatCard({ title, value, icon, description, trend, variant }: StatCardProps) {
  const getVariantClasses = () => {
    switch (variant) {
      case 'success':
        return 'border-green-200 bg-green-50'
      case 'warning':
        return 'border-orange-200 bg-orange-50'
      case 'destructive':
        return 'border-red-200 bg-red-50'
      default:
        return 'border-gray-200 bg-white'
    }
  }

  const getIconColor = () => {
    switch (variant) {
      case 'success':
        return 'text-green-600'
      case 'warning':
        return 'text-orange-600'
      case 'destructive':
        return 'text-red-600'
      default:
        return 'text-blue-600'
    }
  }

  return (
    <Card className={getVariantClasses()}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className={getIconColor()}>{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-gray-900">{value.toLocaleString()}</div>
        <p className="text-xs text-gray-500 mt-1">{description}</p>
        {trend && (
          <div className={`flex items-center mt-2 text-xs ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
            <TrendingUp className="h-3 w-3 mr-1" />
            {trend.value}% from last week
          </div>
        )}
      </CardContent>
    </Card>
  )
}

