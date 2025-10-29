'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react'
import { ConfirmationModal } from '@/components/shared/ConfirmationModal'
import type { CaseActionForm } from '@/types'

interface ActionButtonsProps {
  caseId: string
  onAction: (action: CaseActionForm) => Promise<void>
  disabled?: boolean
}

export function ActionButtons({ caseId, onAction, disabled = false }: ActionButtonsProps) {
  const [selectedAction, setSelectedAction] = useState<'APPROVE' | 'BLOCK' | 'ESCALATE' | 'REQUEST_INFO' | null>(null)
  const [notes, setNotes] = useState('')

  const handleAction = async (notes?: string) => {
    if (!selectedAction) return

    await onAction({
      action: selectedAction,
      reason: notes || '',
      notes,
    })

    setSelectedAction(null)
    setNotes('')
  }

  const actions = [
    {
      type: 'APPROVE' as const,
      label: 'Approve Payment',
      description: 'Allow transaction to proceed',
      icon: CheckCircle,
      variant: 'default' as const,
      color: 'bg-success hover:bg-success/90',
    },
    {
      type: 'BLOCK' as const,
      label: 'Block Payment',
      description: 'Prevent transaction from proceeding',
      icon: XCircle,
      variant: 'destructive' as const,
      color: '',
    },
    {
      type: 'ESCALATE' as const,
      label: 'Escalate to Manager',
      description: 'Send to senior analyst for review',
      icon: AlertTriangle,
      variant: 'outline' as const,
      color: '',
    },
    {
      type: 'REQUEST_INFO' as const,
      label: 'Request More Info',
      description: 'Contact customer for clarification',
      icon: Info,
      variant: 'outline' as const,
      color: '',
    },
  ]

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
          <CardDescription>Decide on case outcome</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Action Buttons */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {actions.map((action) => (
              <Button
                key={action.type}
                variant={action.variant}
                className={action.color || ''}
                onClick={() => setSelectedAction(action.type)}
                disabled={disabled}
              >
                <action.icon className="h-4 w-4 mr-2" />
                {action.label}
              </Button>
            ))}
          </div>

          {/* Analyst Notes */}
          <div className="space-y-2 pt-4 border-t">
            <Label htmlFor="notes">Analyst Notes</Label>
            <Textarea
              id="notes"
              placeholder="Add your analysis, reasoning, or additional context..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              disabled={disabled}
            />
            <p className="text-xs text-muted-foreground">
              Notes will be recorded in the audit trail
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Confirmation Modals */}
      <ConfirmationModal
        open={selectedAction === 'APPROVE'}
        onOpenChange={(open) => !open && setSelectedAction(null)}
        title="Approve Payment"
        description="This will allow the transaction to proceed. This action cannot be undone."
        confirmLabel="Approve"
        variant="default"
        onConfirm={handleAction}
        requireNotes={true}
        notesLabel="Approval Reason"
        notesPlaceholder="Explain why you're approving this payment..."
      />

      <ConfirmationModal
        open={selectedAction === 'BLOCK'}
        onOpenChange={(open) => !open && setSelectedAction(null)}
        title="Block Payment"
        description="This will prevent the transaction from proceeding and notify the customer. This is a critical action that requires justification."
        confirmLabel="Block Payment"
        variant="destructive"
        onConfirm={handleAction}
        requireNotes={true}
        notesLabel="Block Reason"
        notesPlaceholder="Provide detailed reasoning for blocking this payment..."
      />

      <ConfirmationModal
        open={selectedAction === 'ESCALATE'}
        onOpenChange={(open) => !open && setSelectedAction(null)}
        title="Escalate to Manager"
        description="This case will be assigned to a senior analyst for review. Include context to help them make an informed decision."
        confirmLabel="Escalate"
        variant="default"
        onConfirm={handleAction}
        requireNotes={true}
        notesLabel="Escalation Reason"
        notesPlaceholder="Explain why this case needs escalation..."
      />

      <ConfirmationModal
        open={selectedAction === 'REQUEST_INFO'}
        onOpenChange={(open) => !open && setSelectedAction(null)}
        title="Request More Information"
        description="The customer will be contacted for additional information. Specify what information you need."
        confirmLabel="Send Request"
        variant="default"
        onConfirm={handleAction}
        requireNotes={true}
        notesLabel="Information Needed"
        notesPlaceholder="What additional information do you need from the customer?"
      />
    </>
  )
}

