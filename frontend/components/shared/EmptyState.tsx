import { LucideIcon, FileQuestion, Search, Database, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export function EmptyState({
  icon: Icon = FileQuestion,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center p-12 text-center', className)}>
      <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-sm mb-6">{description}</p>
      {action && (
        <Button onClick={action.onClick} variant="default">
          {action.label}
        </Button>
      )}
    </div>
  )
}

export function NoCasesFound() {
  return (
    <EmptyState
      icon={FileQuestion}
      title="No cases found"
      description="There are no cases matching your current filters. Try adjusting your search criteria or clearing filters."
    />
  )
}

export function NoSearchResults() {
  return (
    <EmptyState
      icon={Search}
      title="No results found"
      description="We couldn't find any results matching your search. Try different keywords or check your spelling."
    />
  )
}

export function NoDataAvailable() {
  return (
    <EmptyState
      icon={Database}
      title="No data available"
      description="There is no data available to display at this time. Data will appear here once it becomes available."
    />
  )
}

export function ErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <EmptyState
      icon={AlertCircle}
      title="Unable to load data"
      description="We encountered an error while loading the data. Please try again."
      action={onRetry ? { label: 'Retry', onClick: onRetry } : undefined}
    />
  )
}

