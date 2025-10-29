import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from './useWebSocket'
import type { WebSocketMessage, CaseUpdateMessage } from '@/types'
import toast from 'react-hot-toast'

export function useCaseUpdates() {
  const queryClient = useQueryClient()

  const handleMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'CASE_UPDATED':
        handleCaseUpdate(message.payload as CaseUpdateMessage)
        break
      case 'NEW_CASE':
        handleNewCase(message.payload)
        break
      case 'NOTIFICATION':
        handleNotification(message.payload)
        break
      default:
        break
    }
  }

  const handleCaseUpdate = (update: CaseUpdateMessage) => {
    // Invalidate case queries to trigger refetch
    queryClient.invalidateQueries({ queryKey: ['case', update.case_id] })
    queryClient.invalidateQueries({ queryKey: ['cases'] })

    toast.success(`Case ${update.case_id} updated by ${update.updated_by}`)
  }

  const handleNewCase = (caseData: any) => {
    queryClient.invalidateQueries({ queryKey: ['cases'] })
    queryClient.invalidateQueries({ queryKey: ['dashboardStats'] })

    if (caseData.risk_score > 80) {
      toast.error(`High-risk case created: ${caseData.case_id}`, {
        duration: 5000,
      })
    }
  }

  const handleNotification = (notification: any) => {
    queryClient.invalidateQueries({ queryKey: ['notifications'] })

    if (notification.priority === 'HIGH') {
      toast(notification.message, {
        icon: '⚠️',
        duration: 5000,
      })
    }
  }

  const { isConnected, reconnect } = useWebSocket({
    onMessage: handleMessage,
    onError: (error) => {
      console.error('WebSocket error in case updates:', error)
      toast.error('Real-time updates disconnected')
    },
    onOpen: () => {
      console.log('Real-time case updates connected')
    },
  })

  return { isConnected, reconnect }
}

