'use client'

import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import Link from 'next/link'

interface ErrorDisplayProps {
  error?: Error | string
  title?: string
  message?: string
  onRetry?: () => void
  showHomeButton?: boolean
  showReportButton?: boolean
}

export function ErrorDisplay({
  error,
  title = 'Something went wrong',
  message,
  onRetry,
  showHomeButton = true,
  showReportButton = false,
}: ErrorDisplayProps) {
  const errorMessage = message || (typeof error === 'string' ? error : error?.message) || 'An unexpected error occurred'

  return (
    <div className="flex items-center justify-center min-h-[400px] p-6">
      <div className="max-w-md w-full space-y-4">
        <div className="flex justify-center">
          <div className="h-16 w-16 rounded-full bg-destructive/10 flex items-center justify-center">
            <AlertTriangle className="h-8 w-8 text-destructive" />
          </div>
        </div>

        <div className="text-center space-y-2">
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-muted-foreground">{errorMessage}</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {onRetry && (
            <Button onClick={onRetry} variant="default">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          )}
          {showHomeButton && (
            <Link href="/">
              <Button variant="outline">
                <Home className="h-4 w-4 mr-2" />
                Go Home
              </Button>
            </Link>
          )}
          {showReportButton && (
            <Button variant="outline" size="sm">
              <Bug className="h-4 w-4 mr-2" />
              Report Issue
            </Button>
          )}
        </div>

        {process.env.NODE_ENV === 'development' && error instanceof Error && error.stack && (
          <details className="mt-4">
            <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
              Error Details (Dev Only)
            </summary>
            <pre className="mt-2 text-xs bg-muted p-3 rounded-md overflow-auto max-h-48">
              {error.stack}
            </pre>
          </details>
        )}
      </div>
    </div>
  )
}

export function InlineError({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Alert variant="destructive">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription className="flex items-center justify-between">
        <span>{message}</span>
        {onRetry && (
          <Button variant="ghost" size="sm" onClick={onRetry}>
            <RefreshCw className="h-3 w-3 mr-1" />
            Retry
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}

export function APIErrorDisplay({ error }: { error: Error }) {
  const is404 = error.message.includes('404') || error.message.includes('not found')
  const is403 = error.message.includes('403') || error.message.includes('Forbidden')
  const is401 = error.message.includes('401') || error.message.includes('Unauthorized')

  let title = 'API Error'
  let message = error.message

  if (is404) {
    title = 'Resource Not Found'
    message = 'The requested resource could not be found.'
  } else if (is403) {
    title = 'Access Denied'
    message = 'You do not have permission to access this resource.'
  } else if (is401) {
    title = 'Authentication Required'
    message = 'Please log in to access this resource.'
  }

  return (
    <ErrorDisplay
      title={title}
      message={message}
      showHomeButton={true}
      showReportButton={!is404 && !is403 && !is401}
    />
  )
}

