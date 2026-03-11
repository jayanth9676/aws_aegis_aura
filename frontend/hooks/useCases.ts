/**
 * useCases Hook - Manages fraud cases
 */

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import type { CaseQuery, Case } from '@/types'

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
      const query: CaseQuery = {}
      if (filters) {
        query.page_size = filters.limit
        if (filters.status) query.filters = { status: [filters.status as any] } // bypass mismatch if any
      }
      const data = await apiClient.getCases(query)
      setCases(data.items || [])
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

