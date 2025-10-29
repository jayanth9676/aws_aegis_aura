/**
 * useCases Hook - Manages fraud cases
 */

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'

export type CasePriority = 'HIGH' | 'MEDIUM' | 'LOW'
export type CaseStatus = 'NEW' | 'INVESTIGATING' | 'ESCALATED' | 'RESOLVED' | 'CLOSED'

export interface Case {
  case_id: string
  transaction_id: string
  customer_id: string
  risk_score: number
  confidence: number
  status: CaseStatus | string
  priority: CasePriority | string
  created_at: string
  updated_at?: string
  evidence?: any
  decision?: any
}

interface CaseFilters {
  status?: string
  priority?: string
  limit?: number
}

export function useCases(filters?: CaseFilters) {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadCases()
  }, [filters?.status, filters?.priority, filters?.limit])

  const loadCases = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getCases(filters)
      setCases(data.cases || [])
    } catch (err: any) {
      setError(err.message || 'Failed to load cases')
      console.error('Error loading cases:', err)
    } finally {
      setLoading(false)
    }
  }

  const refresh = () => {
    loadCases()
  }

  return {
    cases,
    loading,
    error,
    refresh
  }
}

