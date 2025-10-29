'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Copy, ExternalLink, CreditCard, User, Smartphone, MapPin } from 'lucide-react'
import Link from 'next/link'
import type { Transaction } from '@/types'
import { useState } from 'react'

interface TransactionSummaryProps {
  transaction: Transaction
  customerName?: string
}

export function TransactionSummary({ transaction, customerName }: TransactionSummaryProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    const details = `
Transaction ID: ${transaction.transaction_id}
Customer: ${customerName || transaction.customer_id}
Amount: ${transaction.currency} ${transaction.amount.toLocaleString()}
Payee: ${transaction.payee_name} (${transaction.payee_account})
Date: ${new Date(transaction.timestamp).toLocaleString()}
Channel: ${transaction.channel}
Payment Method: ${transaction.payment_method}
    `.trim()

    navigator.clipboard.writeText(details)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Transaction Details</CardTitle>
            <CardDescription>Payment information and metadata</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="h-4 w-4 mr-2" />
            {copied ? 'Copied!' : 'Copy'}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Amount */}
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-bold text-foreground">
            {transaction.currency} {transaction.amount.toLocaleString()}
          </span>
          <Badge variant={
            transaction.status === 'COMPLETED' ? 'outline' :
            transaction.status === 'BLOCKED' ? 'destructive' :
            'secondary'
          }>
            {transaction.status}
          </Badge>
        </div>

        {/* Transaction ID */}
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Transaction ID</p>
          <p className="font-mono text-sm">{transaction.transaction_id}</p>
        </div>

        {/* Payee Information */}
        <div className="space-y-3 pt-4 border-t">
          <div className="flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-muted-foreground" />
            <p className="text-sm font-medium">Payee Details</p>
          </div>
          <div className="space-y-2 pl-6">
            <div>
              <p className="text-xs text-muted-foreground">Name</p>
              <p className="text-sm font-medium">{transaction.payee_name}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Account Number</p>
              <p className="text-sm font-mono">{transaction.payee_account}</p>
            </div>
            {transaction.payee_sort_code && (
              <div>
                <p className="text-xs text-muted-foreground">Sort Code</p>
                <p className="text-sm font-mono">{transaction.payee_sort_code}</p>
              </div>
            )}
          </div>
        </div>

        {/* Customer Information */}
        <div className="space-y-3 pt-4 border-t">
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <p className="text-sm font-medium">Customer</p>
          </div>
          <div className="space-y-2 pl-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Customer ID</p>
                <p className="text-sm font-medium">{transaction.customer_id}</p>
              </div>
              <Link href={`/analyst/customers/${transaction.customer_id}`}>
                <Button variant="ghost" size="sm">
                  <ExternalLink className="h-3 w-3 mr-1" />
                  View Profile
                </Button>
              </Link>
            </div>
            {customerName && (
              <div>
                <p className="text-xs text-muted-foreground">Name</p>
                <p className="text-sm font-medium">{customerName}</p>
              </div>
            )}
          </div>
        </div>

        {/* Payment Details */}
        <div className="space-y-3 pt-4 border-t">
          <p className="text-sm font-medium">Payment Information</p>
          <div className="grid grid-cols-2 gap-4 pl-6">
            <div>
              <p className="text-xs text-muted-foreground">Channel</p>
              <Badge variant="outline" className="mt-1">
                {transaction.channel}
              </Badge>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Method</p>
              <Badge variant="outline" className="mt-1">
                {transaction.payment_method}
              </Badge>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Timestamp</p>
              <p className="text-sm">{new Date(transaction.timestamp).toLocaleString()}</p>
            </div>
          </div>
        </div>

        {/* Device Information */}
        {transaction.device_info && (
          <div className="space-y-3 pt-4 border-t">
            <div className="flex items-center gap-2">
              <Smartphone className="h-4 w-4 text-muted-foreground" />
              <p className="text-sm font-medium">Device Information</p>
            </div>
            <div className="grid grid-cols-2 gap-4 pl-6">
              <div>
                <p className="text-xs text-muted-foreground">Device Type</p>
                <p className="text-sm">{transaction.device_info.device_type}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">OS</p>
                <p className="text-sm">{transaction.device_info.os}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Browser</p>
                <p className="text-sm">{transaction.device_info.browser}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">IP Address</p>
                <p className="text-sm font-mono">{transaction.device_info.ip_address}</p>
              </div>
              {transaction.device_info.location && (
                <div className="col-span-2">
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    Location
                  </p>
                  <p className="text-sm">
                    {transaction.device_info.location.city}, {transaction.device_info.location.country}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Behavioral Signals */}
        {transaction.behavioral_signals && (
          <div className="space-y-3 pt-4 border-t">
            <p className="text-sm font-medium">Behavioral Signals</p>
            <div className="grid grid-cols-2 gap-4 pl-6 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">Active Call</p>
                <Badge variant={transaction.behavioral_signals.active_call ? 'destructive' : 'outline'}>
                  {transaction.behavioral_signals.active_call ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Hesitation Score</p>
                <p className="font-medium">
                  {transaction.behavioral_signals.hesitation_score.toFixed(2)}
                </p>
              </div>
              {transaction.behavioral_signals.anomaly_score !== undefined && (
                <div>
                  <p className="text-xs text-muted-foreground">Anomaly Score</p>
                  <p className="font-medium">
                    {transaction.behavioral_signals.anomaly_score.toFixed(2)}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

