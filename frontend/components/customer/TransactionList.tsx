'use client'

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, Clock, AlertTriangle, XCircle } from 'lucide-react'
import Link from 'next/link'
import type { Transaction } from '@/types'
import { cn } from '@/lib/utils'

interface TransactionListProps {
  transactions: Transaction[]
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'COMPLETED':
      return <CheckCircle className="h-5 w-5 text-success" />
    case 'PENDING':
    case 'CHALLENGED':
      return <Clock className="h-5 w-5 text-warning" />
    case 'BLOCKED':
      return <XCircle className="h-5 w-5 text-destructive" />
    default:
      return <AlertTriangle className="h-5 w-5 text-muted-foreground" />
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case 'COMPLETED':
      return 'bg-success/10 text-success border-success/20'
    case 'PENDING':
    case 'CHALLENGED':
      return 'bg-warning/10 text-warning border-warning/20'
    case 'BLOCKED':
      return 'bg-destructive/10 text-destructive border-destructive/20'
    default:
      return 'bg-muted text-muted-foreground border-border'
  }
}

export function TransactionList({ transactions }: TransactionListProps) {
  return (
    <div className="space-y-4">
      {transactions.map((transaction) => (
        <Card
          key={transaction.transaction_id}
          className={cn(
            'p-4 hover:shadow-md transition-all cursor-pointer',
            transaction.risk_score && transaction.risk_score > 70 && 'border-destructive/50'
          )}
        >
          <Link href={transaction.status === 'CHALLENGED' ? `/customer/dialogue/${transaction.transaction_id}` : '#'}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {getStatusIcon(transaction.status)}
                <div>
                  <p className="font-semibold text-foreground">{transaction.payee_name}</p>
                  <p className="text-sm text-muted-foreground">
                    {new Date(transaction.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="text-right">
                <p className="text-2xl font-bold text-foreground">
                  {transaction.currency} {transaction.amount.toLocaleString()}
                </p>
                <Badge className={getStatusColor(transaction.status)}>
                  {transaction.status.replace(/_/g, ' ')}
                </Badge>
              </div>
            </div>

            {transaction.status === 'CHALLENGED' && transaction.risk_score && transaction.risk_score > 70 && (
              <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-destructive mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-destructive mb-1">
                      ⚠️ Security Alert: High Risk Transaction
                    </p>
                    <p className="text-sm text-destructive/90 mb-3">
                      This transaction has been flagged by our AI fraud detection system.
                      Please verify before proceeding.
                    </p>
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-destructive text-destructive-foreground rounded-md text-sm font-semibold">
                      Verify Transaction →
                    </div>
                  </div>
                </div>
              </div>
            )}
          </Link>
        </Card>
      ))}
    </div>
  )
}

