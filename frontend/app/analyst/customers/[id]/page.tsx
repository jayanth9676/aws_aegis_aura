'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Loader2, ArrowLeft, ArrowUpRight, ArrowDownRight, Phone, Mail, MapPin, Building, ShieldAlert, CheckCircle, Clock } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import Link from 'next/link'
import { Customer, Transaction, Case } from '@/types'

interface CustomerPageProps {
  params: { id: string }
}

export default function CustomerProfilePage({ params }: CustomerPageProps) {
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [cases, setCases] = useState<Case[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [custRes, txRes, caseRes] = await Promise.all([
          apiClient.getCustomer(params.id),
          apiClient.getCustomerTransactions(params.id),
          apiClient.getCustomerCases(params.id)
        ])
        setCustomer(custRes)
        setTransactions(txRes)
        setCases(caseRes)
      } catch (e) {
        console.error("Failed to load customer profile", e)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [params.id])

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!customer) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold">Customer Not Found</h2>
          <p className="text-muted-foreground mt-2">The customer ID provided was not found in the system.</p>
          <Link href="/analyst">
            <Button className="mt-4">Return to Dashboard</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/analyst">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Customer Profile</h1>
          <p className="text-muted-foreground mt-1">Detailed view of customer history, transactions, and risk scores</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Customer Details Card */}
        <Card className="md:col-span-1 border-2 shadow-sm">
          <CardHeader>
            <CardTitle className="text-xl">Profile Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col items-center pb-6 border-b">
              <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-2xl mb-3">
                {customer.first_name[0]}{customer.last_name[0]}
              </div>
              <h2 className="text-2xl font-semibold">{customer.first_name} {customer.last_name}</h2>
              <Badge variant="outline" className="mt-2 text-xs">ID: {customer.customer_id}</Badge>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <span className="text-sm">{customer.email}</span>
              </div>
              <div className="flex items-center gap-3">
                <Phone className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <span className="text-sm">{customer.phone}</span>
              </div>
              <div className="flex items-start gap-3">
                <MapPin className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                <span className="text-sm">
                  {customer.address.street}<br />
                  {customer.address.city}, {customer.address.postal_code}<br />
                  {customer.address.country}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <Building className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <span className="text-sm">Registered: {new Date(customer.account_created_date).toLocaleDateString()}</span>
              </div>
            </div>

            <div className="pt-4 border-t">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Risk Score</span>
                <span className="text-sm font-bold text-destructive">{customer.risk_score}/100</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${customer.risk_score > 70 ? 'bg-destructive' : customer.risk_score > 40 ? 'bg-warning' : 'bg-success'}`}
                  style={{ width: `${customer.risk_score}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="md:col-span-2 space-y-6">
          {/* Cases Card */}
          <Card className="border-2 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between py-4">
              <div>
                <CardTitle>Case History</CardTitle>
                <CardDescription>Recent investigations for this customer</CardDescription>
              </div>
              <Badge variant="secondary">{cases.length} Total</Badge>
            </CardHeader>
            <CardContent>
              {cases.length === 0 ? (
                <div className="text-center py-6 text-muted-foreground">No cases found for this customer.</div>
              ) : (
                <div className="space-y-3">
                  {cases.map(caseItem => (
                    <div key={caseItem.case_id} className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full ${caseItem.status === 'NEW' ? 'bg-amber-100 text-amber-600' : caseItem.status === 'CLOSED' ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'}`}>
                          {caseItem.status === 'NEW' ? <AlertTriangle className="h-4 w-4" /> : caseItem.status === 'CLOSED' ? <CheckCircle className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
                        </div>
                        <div>
                          <div className="font-medium text-sm">Case #{caseItem.case_id.split('-')[1] || caseItem.case_id}</div>
                          <div className="text-xs text-muted-foreground">{new Date(caseItem.created_at).toLocaleDateString()}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <Badge variant="outline" className={caseItem.risk_score > 80 ? 'border-destructive text-destructive' : ''}>
                          Risk {caseItem.risk_score}
                        </Badge>
                        <Link href={`/analyst/cases/${caseItem.case_id}`}>
                          <Button variant="ghost" size="sm">View</Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Transactions Card */}
          <Card className="border-2 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between py-4">
              <div>
                <CardTitle>Transaction History</CardTitle>
                <CardDescription>Recent transfers and payments</CardDescription>
              </div>
              <Badge variant="secondary">{transactions.length} Total</Badge>
            </CardHeader>
            <CardContent>
              {transactions.length === 0 ? (
                <div className="text-center py-6 text-muted-foreground">No transactions found for this customer.</div>
              ) : (
                <div className="space-y-3">
                  {transactions.slice(0, 10).map(tx => (
                    <div key={tx.transaction_id} className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-full bg-slate-100 text-slate-600">
                          {tx.sender_account === customer.customer_id ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                        </div>
                        <div>
                          <div className="font-medium text-sm">{tx.payee_name}</div>
                          <div className="text-xs text-muted-foreground font-mono">{tx.payee_account}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`font-medium ${tx.sender_account === customer.customer_id ? 'text-slate-900 dark:text-slate-200' : 'text-success'}`}>
                          {tx.sender_account === customer.customer_id ? '-' : '+'}${tx.amount.toFixed(2)}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {new Date(tx.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                  {transactions.length > 10 && (
                    <div className="text-center pt-2">
                      <Button variant="link" size="sm">View all transactions</Button>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
