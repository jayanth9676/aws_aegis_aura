'use client'

import { MainLayout } from '@/components/layout/MainLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TransactionList } from '@/components/customer/TransactionList'
import { SecurityAlert } from '@/components/customer/SecurityAlert'
import { ScamEducation } from '@/components/customer/ScamEducation'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Shield, AlertTriangle, Phone, HelpCircle, Settings } from 'lucide-react'
import { useState, useEffect } from 'react'
import type { Transaction } from '@/types'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { Loader2 } from 'lucide-react'

const fallbackTransactions: Transaction[] = [
  {
    id: 'TXN-8521',
    transaction_id: 'TXN-8521',
    customer_id: 'CUST-001',
    amount: 8500,
    currency: '£',
    payee_name: 'Unknown Investment Ltd',
    payee_account: '12345678',
    timestamp: new Date().toISOString(),
    status: 'CHALLENGED',
    risk_score: 92,
    channel: 'WEB',
    payment_method: 'FASTER_PAYMENT',
  }
]

export default function CustomerDashboard() {
  const [showEducation, setShowEducation] = useState(false)
  
  const { data: transactions = [], isLoading } = useQuery({
    queryKey: ['customer-transactions', 'CUST-001'],
    queryFn: () => apiClient.getCustomerTransactions('CUST-001'),
  })

  // Use fallback if no real transactions yet so the UI isn't completely empty
  const displayTransactions = transactions.length > 0 ? transactions : fallbackTransactions
  
  const hasHighRiskTransaction = displayTransactions.some(t => t.risk_score && t.risk_score > 70)
  const challengedTransactions = displayTransactions.filter(t => t.status === 'CHALLENGED' || (t.risk_score && t.risk_score > 70))
  const latestChallenged = challengedTransactions[0]

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-primary to-primary/80 rounded-lg p-6 text-primary-foreground">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Welcome back, Sarah</h1>
              <p className="text-primary-foreground/90">
                Your account is protected by AI-powered fraud detection
              </p>
            </div>
            <Shield className="h-16 w-16 opacity-20" />
          </div>
        </div>

        {/* Security Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-full bg-success/10 flex items-center justify-center">
                  <Shield className="h-6 w-6 text-success" />
                </div>
                <div>
                  <p className="text-2xl font-bold">Protected</p>
                  <p className="text-sm text-muted-foreground">AI Fraud Detection Active</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-full bg-info/10 flex items-center justify-center">
                  <Badge className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{displayTransactions.length}</p>
                  <p className="text-sm text-muted-foreground">Recent Transactions</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className={`h-12 w-12 rounded-full flex items-center justify-center ${hasHighRiskTransaction ? 'bg-warning/10' : 'bg-muted'
                  }`}>
                  <AlertTriangle className={`h-6 w-6 ${hasHighRiskTransaction ? 'text-warning' : 'text-muted-foreground'}`} />
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {challengedTransactions.length}
                  </p>
                  <p className="text-sm text-muted-foreground">Pending Verification</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {hasHighRiskTransaction && latestChallenged && (
          <SecurityAlert
            severity="high"
            title={`⚠️ Security Alert: Verification Required for £${latestChallenged.amount}`}
            message={`We've temporarily held your payment to ${latestChallenged.payee_name} for your security. Our AI fraud analysts want to ask you a couple of questions.`}
            onVerify={() => window.location.href = `/customer/dialogue/${latestChallenged.transaction_id}`}
            onLearnMore={() => setShowEducation(true)}
          />
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Button variant="outline" className="h-auto py-4 flex-col gap-2">
            <Phone className="h-5 w-5" />
            <span className="text-sm">Contact Support</span>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex-col gap-2">
            <AlertTriangle className="h-5 w-5" />
            <span className="text-sm">Report Fraud</span>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => setShowEducation(!showEducation)}>
            <HelpCircle className="h-5 w-5" />
            <span className="text-sm">Security Tips</span>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex-col gap-2">
            <Settings className="h-5 w-5" />
            <span className="text-sm">Settings</span>
          </Button>
        </div>

        {/* Recent Transactions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Transactions</CardTitle>
            <CardDescription>Your latest payment activity</CardDescription>
          </CardHeader>
          <CardContent>
            <TransactionList transactions={displayTransactions} />
          </CardContent>
        </Card>

        {/* Educational Content */}
        {showEducation && <ScamEducation />}

        {/* Support Footer */}
        <Card className="bg-muted/50">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-muted-foreground mb-2">
                Need help or see something suspicious?
              </p>
              <p className="font-semibold">
                Call us 24/7 on <span className="text-primary">0800-123-4567</span>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
