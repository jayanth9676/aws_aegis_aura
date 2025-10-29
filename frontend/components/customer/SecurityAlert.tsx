'use client'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Shield, Phone, Info } from 'lucide-react'

interface SecurityAlertProps {
  severity?: 'high' | 'medium' | 'low'
  title: string
  message: string
  onVerify?: () => void
  onCancel?: () => void
  onLearnMore?: () => void
}

export function SecurityAlert({
  severity = 'high',
  title,
  message,
  onVerify,
  onCancel,
  onLearnMore,
}: SecurityAlertProps) {
  const severityStyles = {
    high: 'border-destructive bg-destructive/10',
    medium: 'border-warning bg-warning/10',
    low: 'border-info bg-info/10',
  }

  const severityIcons = {
    high: <AlertTriangle className="h-6 w-6 text-destructive" />,
    medium: <AlertTriangle className="h-6 w-6 text-warning" />,
    low: <Shield className="h-6 w-6 text-info" />,
  }

  return (
    <Alert className={severityStyles[severity]}>
      <div className="flex gap-4">
        <div className="flex-shrink-0 mt-1">
          {severityIcons[severity]}
        </div>
        <div className="flex-1 space-y-4">
          <div>
            <AlertTitle className="text-lg font-bold mb-2">{title}</AlertTitle>
            <AlertDescription className="text-sm leading-relaxed">
              {message}
            </AlertDescription>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            {onVerify && (
              <Button onClick={onVerify} variant="default" className="flex-1 sm:flex-none">
                <Shield className="h-4 w-4 mr-2" />
                Verify Transaction
              </Button>
            )}
            {onCancel && (
              <Button onClick={onCancel} variant="destructive" className="flex-1 sm:flex-none">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Cancel Payment
              </Button>
            )}
            {onLearnMore && (
              <Button onClick={onLearnMore} variant="outline" className="flex-1 sm:flex-none">
                <Info className="h-4 w-4 mr-2" />
                Learn More
              </Button>
            )}
          </div>

          <div className="flex items-center gap-2 text-sm text-muted-foreground pt-2 border-t">
            <Phone className="h-4 w-4" />
            <span>
              Need help? Call us at <strong className="text-foreground">0800-123-4567</strong>
            </span>
          </div>
        </div>
      </div>
    </Alert>
  )
}

