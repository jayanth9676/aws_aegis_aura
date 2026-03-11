'use client'

import { useState } from 'react'
import { Dialog } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ConfirmationModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'default' | 'destructive'
  onConfirm: (notes?: string) => void | Promise<void>
  requireNotes?: boolean
  notesLabel?: string
  notesPlaceholder?: string
}

export function ConfirmationModal({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  onConfirm,
  requireNotes = false,
  notesLabel = 'Notes',
  notesPlaceholder = 'Add any additional notes...',
}: ConfirmationModalProps) {
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)

  const handleConfirm = async () => {
    if (requireNotes && !notes.trim()) {
      return
    }

    setLoading(true)
    try {
      await onConfirm(notes || undefined)
      onOpenChange(false)
      setNotes('')
    } catch (error) {
      console.error('Confirmation action failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    if (!loading) {
      onOpenChange(false)
      setNotes('')
    }
  }

  return (
    <Dialog
      open={open}
      onClose={handleCancel}
      title={title}
    >
      <div className="space-y-4">
        <div className="flex items-start gap-4">
          {variant === 'destructive' && (
            <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
          )}
          <p className="text-gray-700 dark:text-gray-300">{description}</p>
        </div>

        {requireNotes && (
          <div className="space-y-2 mt-4">
            <Label htmlFor="notes">{notesLabel}</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={notesPlaceholder}
              rows={4}
              disabled={loading}
              className="w-full"
            />
          </div>
        )}

        <div className="flex justify-end gap-2 mt-6">
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={loading}
          >
            {cancelLabel}
          </Button>
          <Button
            variant={variant === 'destructive' ? 'destructive' : 'default'}
            onClick={handleConfirm}
            disabled={loading || (requireNotes && !notes.trim())}
            className={cn(loading && 'cursor-not-allowed')}
          >
            {loading ? 'Processing...' : confirmLabel}
          </Button>
        </div>
      </div>
    </Dialog>
  )
}

