'use client'

import { useQuery } from '@tanstack/react-query'
import { MainLayout } from '@/components/layout/MainLayout'
import { CaseHeader } from '@/components/analyst/case-details/CaseHeader'
import { TransactionSummary } from '@/components/analyst/case-details/TransactionSummary'
import { RiskAssessment } from '@/components/analyst/case-details/RiskAssessment'
import { EvidenceTimeline } from '@/components/analyst/case-details/EvidenceTimeline'
import { AgentReasoning } from '@/components/analyst/case-details/AgentReasoning'
import { ActionButtons } from '@/components/analyst/case-details/ActionButtons'
import { NetworkGraph } from '@/components/visualizations/NetworkGraph'
import { SHAPChart } from '@/components/visualizations/SHAPChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { apiClient } from '@/lib/api-client'
import { CaseDetailsSkeleton } from '@/components/shared/Loading'
import { ErrorDisplay } from '@/components/shared/ErrorDisplay'
import type { CaseActionForm, Transaction } from '@/types'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

interface CaseDetailsPageProps {
  params: { id: string }
}

export default function CaseDetailsPage({ params }: CaseDetailsPageProps) {
  const router = useRouter()
  const [actionInProgress, setActionInProgress] = useState(false)

  // Fetch case details
  const { data: caseData, isLoading, error, refetch } = useQuery({
    queryKey: ['case', params.id],
    queryFn: () => apiClient.getCase(params.id),
  })

  // Fetch transaction details if available
  const { data: transaction } = useQuery<Transaction>({
    queryKey: ['transaction', caseData?.transaction_id],
    queryFn: () => apiClient.getTransaction(caseData!.transaction_id),
    enabled: !!caseData?.transaction_id,
  })

  // Fetch network graph data
  const { data: networkData } = useQuery({
    queryKey: ['case-network', params.id],
    queryFn: () => apiClient.getCaseNetworkGraph(params.id),
    enabled: !!caseData,
  })

  // Fetch SHAP explanation
  const { data: shapData } = useQuery({
    queryKey: ['case-shap', params.id],
    queryFn: () => apiClient.getCaseSHAPExplanation(params.id),
    enabled: !!caseData,
  })

  const handleCaseAction = async (action: CaseActionForm) => {
    setActionInProgress(true)
    try {
      await apiClient.caseAction(params.id, action)
      toast.success(`Case ${action.action.toLowerCase()}d successfully`)
      refetch()
    } catch (error) {
      toast.error(`Failed to ${action.action.toLowerCase()} case`)
      console.error('Case action failed:', error)
    } finally {
      setActionInProgress(false)
    }
  }

  const handleApprove = () => {
    handleCaseAction({ action: 'APPROVE', reason: 'Approved after review' })
  }

  const handleBlock = () => {
    handleCaseAction({ action: 'BLOCK', reason: 'Blocked due to high fraud risk' })
  }

  const handleEscalate = () => {
    handleCaseAction({ action: 'ESCALATE', reason: 'Escalated for senior review' })
  }

  const handleClose = () => {
    handleCaseAction({ action: 'APPROVE', reason: 'Case closed' })
  }

  if (isLoading) {
    return (
      <MainLayout>
        <CaseDetailsSkeleton />
      </MainLayout>
    )
  }

  if (error || !caseData) {
    return (
      <MainLayout>
        <div className="p-6">
          <ErrorDisplay
            error={error as Error}
            title="Failed to load case"
            message="The case could not be found or there was an error loading it."
            onRetry={() => refetch()}
          />
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="p-6 space-y-6">
        {/* Case Header */}
        <CaseHeader
          caseData={caseData}
          onApprove={handleApprove}
          onBlock={handleBlock}
          onEscalate={handleEscalate}
          onClose={handleClose}
        />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Transaction & Risk */}
          <div className="lg:col-span-2 space-y-6">
            {/* Transaction Summary */}
            {transaction && (
              <TransactionSummary transaction={transaction} customerName={caseData.customer_id} />
            )}

          {/* Risk Assessment */}
            <RiskAssessment caseData={caseData} />

            {/* Tabbed Content */}
            <Tabs defaultValue="timeline" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="timeline">Evidence Timeline</TabsTrigger>
                <TabsTrigger value="reasoning">Agent Reasoning</TabsTrigger>
              </TabsList>
              <TabsContent value="timeline" className="mt-6">
                <EvidenceTimeline events={caseData.timeline || []} />
              </TabsContent>
              <TabsContent value="reasoning" className="mt-6">
                <AgentReasoning reasoning={caseData.agent_reasoning || []} />
              </TabsContent>
            </Tabs>
          </div>

          {/* Right Column - Actions */}
          <div className="lg:col-span-1 space-y-6">
            <ActionButtons
              caseId={params.id}
              onAction={handleCaseAction}
              disabled={actionInProgress}
            />
          </div>
        </div>

        {/* Full Width Visualizations */}
        <div className="space-y-6">
          {/* Network Graph */}
          {networkData && (
            <Card>
              <CardHeader>
                <CardTitle>Network Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <NetworkGraph data={networkData} />
              </CardContent>
            </Card>
          )}

          {/* SHAP Explanation */}
          {shapData && (
            <Card>
              <CardHeader>
                <CardTitle>Model Explainability (SHAP Values)</CardTitle>
              </CardHeader>
              <CardContent>
                <SHAPChart data={shapData} />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </MainLayout>
  )
}
