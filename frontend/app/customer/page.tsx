'use client'

import { MainLayout } from '@/components/layout/MainLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TransactionList } from '@/components/customer/TransactionList'
import { SecurityAlert } from '@/components/customer/SecurityAlert'
import { ScamEducation } from '@/components/customer/ScamEducation'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Shield, AlertTriangle, Phone, HelpCircle, Settings } from 'lucide-react'
import { useState } from 'react'
import type { Transaction } from '@/types'

// Mock data
const mockTransactions: Transaction[] = [
  {
    transaction_id: 'TXN-8521',
    customer_id: 'CUST-001',
    amount: 8500,
    currency: '£',
    payee_name: 'Unknown Investment Ltd',
    payee_account: '12345678',
    timestamp: new Date().toISOString(),
    status: 'CHALLENGED',
    risk_score: 92,
    channel: 'ONLINE',
    payment_method: 'BANK_TRANSFER',
  },
  {
    transaction_id: 'TXN-8520',
    customer_id: 'CUST-001',
    amount: 125.50,
    currency: '£',
    payee_name: 'Tesco Stores',
    payee_account: '87654321',
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    status: 'COMPLETED',
    channel: 'ONLINE',
    payment_method: 'DEBIT_CARD',
  },
  {
    transaction_id: 'TXN-8519',
    customer_id: 'CUST-001',
    amount: 45.00,
    currency: '£',
    payee_name: 'Amazon UK',
    payee_account: '11223344',
    timestamp: new Date(Date.now() - 172800000).toISOString(),
    status: 'COMPLETED',
    channel: 'ONLINE',
    payment_method: 'DEBIT_CARD',
  },
]

export default function CustomerDashboard() {
  const [showEducation, setShowEducation] = useState(false)
  const hasHighRiskTransaction = mockTransactions.some(t => t.risk_score && t.risk_score > 70)

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
                  <p className="text-2xl font-bold">{mockTransactions.length}</p>
                  <p className="text-sm text-muted-foreground">Recent Transactions</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className={`h-12 w-12 rounded-full flex items-center justify-center ${
                  hasHighRiskTransaction ? 'bg-warning/10' : 'bg-muted'
                }`}>
                  <AlertTriangle className={`h-6 w-6 ${hasHighRiskTransaction ? 'text-warning' : 'text-muted-foreground'}`} />
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {mockTransactions.filter(t => t.status === 'CHALLENGED').length}
                  </p>
                  <p className="text-sm text-muted-foreground">Pending Verification</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* High Risk Alert */}
        {hasHighRiskTransaction && (
          <SecurityAlert
            severity="high"
            title="⚠️ Security Alert: Transaction Verification Required"
            message="We've detected a high-risk transaction that needs your immediate attention. This payment has been temporarily held for your security. Please verify the transaction details before it can proceed."
            onVerify={() => window.location.href = '/customer/dialogue/TXN-8521'}
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
            <TransactionList transactions={mockTransactions} />
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
