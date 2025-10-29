'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { X, Filter, Search } from 'lucide-react'
import { Card } from '@/components/ui/card'
import type { CaseFilters as CaseFiltersType, CaseStatus, RiskLevel } from '@/types'

interface CaseFiltersProps {
  filters: CaseFiltersType
  onFiltersChange: (filters: CaseFiltersType) => void
  onClear: () => void
}

const statusOptions: { value: CaseStatus; label: string }[] = [
  { value: 'NEW', label: 'New' },
  { value: 'INVESTIGATING', label: 'Investigating' },
  { value: 'PENDING_DECISION', label: 'Pending Decision' },
  { value: 'ESCALATED', label: 'Escalated' },
  { value: 'RESOLVED', label: 'Resolved' },
  { value: 'CLOSED', label: 'Closed' },
]

const riskLevelOptions: { value: RiskLevel; label: string; color: string }[] = [
  { value: 'CRITICAL', label: 'Critical', color: 'bg-destructive' },
  { value: 'HIGH', label: 'High', color: 'bg-orange-500' },
  { value: 'MEDIUM', label: 'Medium', color: 'bg-warning' },
  { value: 'LOW', label: 'Low', color: 'bg-success' },
]

export function CaseFilters({ filters, onFiltersChange, onClear }: CaseFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search || '')

  const hasActiveFilters =
    (filters.status && filters.status.length > 0) ||
    (filters.risk_level && filters.risk_level.length > 0) ||
    filters.assigned_analyst ||
    filters.date_from ||
    filters.date_to ||
    filters.search

  const handleStatusToggle = (status: CaseStatus) => {
    const current = filters.status || []
    const newStatus = current.includes(status)
      ? current.filter((s) => s !== status)
      : [...current, status]
    onFiltersChange({ ...filters, status: newStatus.length > 0 ? newStatus : undefined })
  }

  const handleRiskToggle = (risk: RiskLevel) => {
    const current = filters.risk_level || []
    const newRisk = current.includes(risk)
      ? current.filter((r) => r !== risk)
      : [...current, risk]
    onFiltersChange({ ...filters, risk_level: newRisk.length > 0 ? newRisk : undefined })
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onFiltersChange({ ...filters, search: searchInput || undefined })
  }

  return (
    <Card className="p-4">
      <div className="space-y-4">
        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search by case ID, customer name, transaction ID..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button type="submit">Search</Button>
        </form>

        {/* Filter Row */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Filters:</span>
          </div>

          {/* Status Filter */}
          <div className="flex flex-wrap gap-2">
            {statusOptions.map((option) => {
              const isActive = filters.status?.includes(option.value)
              return (
                <Badge
                  key={option.value}
                  variant={isActive ? 'default' : 'outline'}
                  className="cursor-pointer hover:bg-primary/80"
                  onClick={() => handleStatusToggle(option.value)}
                >
                  {option.label}
                  {isActive && <X className="ml-1 h-3 w-3" />}
                </Badge>
              )
            })}
          </div>

          <div className="h-6 w-px bg-border" />

          {/* Risk Level Filter */}
          <div className="flex flex-wrap gap-2">
            {riskLevelOptions.map((option) => {
              const isActive = filters.risk_level?.includes(option.value)
              return (
                <Badge
                  key={option.value}
                  variant={isActive ? 'default' : 'outline'}
                  className="cursor-pointer hover:bg-primary/80"
                  onClick={() => handleRiskToggle(option.value)}
                >
                  <div className={`h-2 w-2 rounded-full ${option.color} mr-1.5`} />
                  {option.label}
                  {isActive && <X className="ml-1 h-3 w-3" />}
                </Badge>
              )
            })}
          </div>

          {hasActiveFilters && (
            <>
              <div className="h-6 w-px bg-border" />
              <Button
                variant="ghost"
                size="sm"
                onClick={onClear}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4 mr-1" />
                Clear all
              </Button>
            </>
          )}
        </div>

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="flex flex-wrap gap-2 pt-2 border-t">
            <span className="text-xs text-muted-foreground">Active filters:</span>
            {filters.status?.map((status) => (
              <Badge key={status} variant="secondary" className="text-xs">
                Status: {status}
                <X
                  className="ml-1 h-3 w-3 cursor-pointer"
                  onClick={() => handleStatusToggle(status)}
                />
              </Badge>
            ))}
            {filters.risk_level?.map((risk) => (
              <Badge key={risk} variant="secondary" className="text-xs">
                Risk: {risk}
                <X
                  className="ml-1 h-3 w-3 cursor-pointer"
                  onClick={() => handleRiskToggle(risk)}
                />
              </Badge>
            ))}
            {filters.search && (
              <Badge variant="secondary" className="text-xs">
                Search: {filters.search}
                <X
                  className="ml-1 h-3 w-3 cursor-pointer"
                  onClick={() => {
                    setSearchInput('')
                    onFiltersChange({ ...filters, search: undefined })
                  }}
                />
              </Badge>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}

