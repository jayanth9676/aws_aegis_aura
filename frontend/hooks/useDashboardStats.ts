/**
 * useDashboardStats Hook - Fetches dashboard statistics
 */

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'

export interface DashboardStats {
  active_cases: number
  high_risk_cases: number
  resolved_today: number
  avg_risk_score: number
  fraud_detection_rate: number
  false_positive_rate: number
}

export function useDashboardStats(refreshInterval?: number) {
  const [stats, setStats] = useState<DashboardStats>({
    active_cases: 0,
    high_risk_cases: 0,
    resolved_today: 0,
    avg_risk_score: 0,
    fraud_detection_rate: 0,
    false_positive_rate: 0
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStats()

    // Auto-refresh if interval is specified
    if (refreshInterval) {
      const interval = setInterval(loadStats, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [refreshInterval])

  const loadStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getDashboardStats()
      setStats(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load stats')
      console.error('Error loading stats:', err)
    } finally {
      setLoading(false)
    }
  }

  return {
    stats,
    loading,
    error,
    refresh: loadStats
  }
}

