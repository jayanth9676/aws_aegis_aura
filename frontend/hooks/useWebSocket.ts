import { useEffect, useRef, useState, useCallback } from 'react'
import type { WebSocketMessage, WebSocketMessageType } from '@/types'

interface UseWebSocketOptions {
  url?: string
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}

interface UseWebSocketReturn {
  sendMessage: (message: WebSocketMessage) => void
  readyState: number
  isConnected: boolean
  reconnect: () => void
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = WS_BASE_URL,
    reconnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options

  const ws = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const reconnectTimeout = useRef<NodeJS.Timeout>()
  const messageQueue = useRef<WebSocketMessage[]>([])

  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING)
  const [isConnected, setIsConnected] = useState(false)

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setReadyState(WebSocket.OPEN)
        setIsConnected(true)
        reconnectAttempts.current = 0

        // Send queued messages
        while (messageQueue.current.length > 0) {
          const msg = messageQueue.current.shift()
          if (msg && ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(msg))
          }
        }

        onOpen?.()
      }

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        onError?.(error)
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setReadyState(WebSocket.CLOSED)
        setIsConnected(false)
        onClose?.()

        // Attempt reconnection
        if (reconnect && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++
          const delay = reconnectInterval * Math.pow(1.5, reconnectAttempts.current - 1)
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`)
          
          reconnectTimeout.current = setTimeout(() => {
            connect()
          }, delay)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }, [url, reconnect, reconnectInterval, maxReconnectAttempts, onOpen, onClose, onError, onMessage])

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    } else {
      // Queue message if not connected
      messageQueue.current.push(message)
    }
  }, [])

  const manualReconnect = useCallback(() => {
    reconnectAttempts.current = 0
    if (ws.current) {
      ws.current.close()
    }
    connect()
  }, [connect])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [connect])

  return {
    sendMessage,
    readyState,
    isConnected,
    reconnect: manualReconnect,
  }
}
