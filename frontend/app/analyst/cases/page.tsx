'use client'

import { useState } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { CaseFilters } from '@/components/analyst/CaseFilters'
import { EnhancedCaseList } from '@/components/analyst/EnhancedCaseList'
import type { CaseFilters as CaseFiltersType } from '@/types'

export default function CasesPage() {
  const [filters, setFilters] = useState<CaseFiltersType>({})

  const handleClearFilters = () => {
    setFilters({})
  }

  return (
    <MainLayout>
      <div className="p-6 space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold">Fraud Cases</h1>
          <p className="text-muted-foreground mt-1">
            Manage and investigate fraud cases
          </p>
        </div>

        {/* Filters */}
        <CaseFilters
          filters={filters}
          onFiltersChange={setFilters}
          onClear={handleClearFilters}
        />

        {/* Case List */}
        <EnhancedCaseList filters={filters} />
      </div>
    </MainLayout>
  )
}

