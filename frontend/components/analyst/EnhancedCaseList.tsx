'use client'

import { useQuery } from '@tanstack/react-query'
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  ColumnDef,
  flexRender,
  SortingState,
} from '@tanstack/react-table'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiClient } from '@/lib/api-client'
import { Eye, ChevronLeft, ChevronRight, RefreshCw, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import Link from 'next/link'
import { TableSkeleton } from '../shared/Loading'
import { ErrorDisplay } from '../shared/ErrorDisplay'
import { NoCasesFound } from '../shared/EmptyState'
import type { Case, CaseFilters as CaseFiltersType } from '@/types'
import { useState } from 'react'
import { cn } from '@/lib/utils'

interface EnhancedCaseListProps {
  filters?: CaseFiltersType
}

const getRiskColor = (score: number) => {
  if (score >= 85) return 'text-destructive'
  if (score >= 60) return 'text-warning'
  return 'text-success'
}

const getRiskBadgeVariant = (score: number) => {
  if (score >= 85) return 'destructive'
  if (score >= 60) return 'default'
  return 'secondary'
}

const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case 'NEW':
      return 'default'
    case 'INVESTIGATING':
      return 'secondary'
    case 'ESCALATED':
      return 'destructive'
    case 'RESOLVED':
    case 'CLOSED':
      return 'outline'
    default:
      return 'secondary'
  }
}

export function EnhancedCaseList({ filters }: EnhancedCaseListProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'created_at', desc: true }
  ])
  const [pageIndex, setPageIndex] = useState(0)
  const pageSize = 20

  // Fetch cases with filters
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['cases', filters, sorting, pageIndex],
    queryFn: () => apiClient.getCases({
      filters,
      sort_by: sorting[0]?.id as any,
      sort_order: sorting[0]?.desc ? 'desc' : 'asc',
      page: pageIndex + 1,
      page_size: pageSize,
    }),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const cases = data?.items || []
  const totalPages = data?.total_pages || 0

  // Define columns
  const columns: ColumnDef<Case>[] = [
    {
      accessorKey: 'case_id',
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="-ml-4"
          >
            Case ID
            {column.getIsSorted() === 'asc' ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === 'desc' ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        )
      },
      cell: ({ row }) => (
        <Link 
          href={`/analyst/cases/${row.original.case_id}`}
          className="text-primary hover:underline font-medium"
        >
          {row.original.case_id}
        </Link>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <Badge variant={getStatusBadgeVariant(row.original.status) as any}>
          {row.original.status.replace(/_/g, ' ')}
        </Badge>
      ),
    },
    {
      accessorKey: 'risk_score',
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="-ml-4"
          >
            Risk Score
            {column.getIsSorted() === 'asc' ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === 'desc' ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        )
      },
      cell: ({ row }) => {
        const score = row.original.risk_score
        if (!score) return <span className="text-muted-foreground">N/A</span>
        
        return (
          <div className="flex items-center gap-2">
            <Badge variant={getRiskBadgeVariant(score) as any} className="font-mono">
              {score}
            </Badge>
          </div>
        )
      },
    },
    {
      accessorKey: 'customer_id',
      header: 'Customer',
      cell: ({ row }) => (
        <div className="text-sm font-medium">
          {row.original.customer_id}
        </div>
      ),
    },
    {
      accessorKey: 'transaction_id',
      header: 'Transaction',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground font-mono">
          {row.original.transaction_id}
        </div>
      ),
    },
    {
      accessorKey: 'assigned_analyst',
      header: 'Assigned To',
      cell: ({ row }) => (
        <div className="text-sm">
          {row.original.assigned_analyst || 'Unassigned'}
        </div>
      ),
    },
    {
      accessorKey: 'created_at',
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="-ml-4"
          >
            Created
            {column.getIsSorted() === 'asc' ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === 'desc' ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        )
      },
      cell: ({ row }) => {
        const date = new Date(row.original.created_at)
        return (
          <div className="text-sm text-muted-foreground">
            {date.toLocaleDateString()} {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <Link href={`/analyst/cases/${row.original.case_id}`}>
          <Button variant="ghost" size="sm">
            <Eye className="h-4 w-4 mr-2" />
            View
          </Button>
        </Link>
      ),
    },
  ]

  const table = useReactTable({
    data: cases,
    columns,
    state: {
      sorting,
      pagination: {
        pageIndex,
        pageSize,
      },
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualPagination: true,
    pageCount: totalPages,
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Fraud Cases</CardTitle>
        </CardHeader>
        <CardContent>
          <TableSkeleton rows={10} columns={7} />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Fraud Cases</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorDisplay
            error={error as Error}
            onRetry={() => refetch()}
            showHomeButton={false}
          />
        </CardContent>
      </Card>
    )
  }

  if (cases.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Fraud Cases</CardTitle>
        </CardHeader>
        <CardContent>
          <NoCasesFound />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Fraud Cases</CardTitle>
            <CardDescription>
              {data?.total || 0} total cases
            </CardDescription>
          </div>
          <Button onClick={() => refetch()} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  className="hover:bg-muted/50 transition-colors"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-6">
          <div className="text-sm text-muted-foreground">
            Showing page {pageIndex + 1} of {totalPages} ({data?.total || 0} total)
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
              onClick={() => setPageIndex(Math.max(0, pageIndex - 1))}
              disabled={pageIndex === 0}
              >
              <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
              onClick={() => setPageIndex(pageIndex + 1)}
              disabled={pageIndex >= totalPages - 1}
              >
                Next
              <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
      </CardContent>
    </Card>
  )
}

