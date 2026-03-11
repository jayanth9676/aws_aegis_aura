'use client'

import { useState, useEffect, useCallback } from 'react'
import { Bell, X, CheckCheck, AlertTriangle, Info, CheckCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import Link from 'next/link'
import type { NotificationMessage } from '@/types'
import { apiClient } from '@/lib/api-client'

interface NotificationCenterProps {
  onClose: () => void
  onUnreadCountChange?: (count: number) => void
}

function getNotificationIcon(type: NotificationMessage['type']) {
  switch (type) {
    case 'WARNING':
      return <AlertTriangle className="h-5 w-5 text-yellow-500" />
    case 'ERROR':
      return <AlertTriangle className="h-5 w-5 text-destructive" />
    case 'SUCCESS':
      return <CheckCircle className="h-5 w-5 text-green-500" />
    case 'INFO':
    default:
      return <Info className="h-5 w-5 text-blue-500" />
  }
}

function getTimeAgo(timestamp: string): string {
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  const diff = now - then

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

export function NotificationCenter({ onClose, onUnreadCountChange }: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<NotificationMessage[]>([])
  const [loading, setLoading] = useState(true)

  const fetchNotifications = useCallback(async () => {
    try {
      const data = await apiClient.getNotifications()
      setNotifications(data)
      const unread = data.filter((n: NotificationMessage) => !n.read).length
      onUnreadCountChange?.(unread)
    } catch (err) {
      // Silently fail - notifications are non-critical
      console.warn('Failed to fetch notifications:', err)
    } finally {
      setLoading(false)
    }
  }, [onUnreadCountChange])

  useEffect(() => {
    fetchNotifications()
    // Poll every 30s for new notifications
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [fetchNotifications])

  const unreadCount = notifications.filter((n) => !n.read).length

  const markAsRead = async (id: string) => {
    try {
      await apiClient.markNotificationRead(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      )
      onUnreadCountChange?.(unreadCount - 1)
    } catch (err) {
      console.warn('Failed to mark read:', err)
      // Optimistic update anyway
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      )
    }
  }

  const markAllAsRead = async () => {
    try {
      await apiClient.markAllNotificationsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
      onUnreadCountChange?.(0)
    } catch (err) {
      console.warn('Failed to mark all read:', err)
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
    }
  }

  return (
    <div className="w-96 rounded-lg border bg-background shadow-lg animate-in slide-in-from-top-2">
      {/* Header */}
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          <h3 className="font-semibold">Notifications</h3>
          {unreadCount > 0 && (
            <Badge variant="secondary" className="rounded-full">
              {unreadCount}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1">
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={markAllAsRead}
              className="text-xs"
            >
              <CheckCheck className="h-4 w-4 mr-1" />
              Mark all read
            </Button>
          )}
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Notifications List */}
      <ScrollArea className="h-[400px]">
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <Bell className="h-12 w-12 text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">No notifications</p>
          </div>
        ) : (
          <div className="divide-y">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={cn(
                  'p-4 transition-colors hover:bg-muted/50 cursor-pointer',
                  !notification.read && 'bg-muted/30'
                )}
                onClick={() => !notification.read && markAsRead(notification.id)}
              >
                {notification.action_url ? (
                  <Link href={notification.action_url} onClick={onClose}>
                    <NotificationContent notification={notification} />
                  </Link>
                ) : (
                  <NotificationContent notification={notification} />
                )}
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Footer */}
      <div className="border-t p-3 text-center">
        <Button
          variant="ghost"
          size="sm"
          className="text-xs w-full"
          onClick={() => { fetchNotifications(); }}
        >
          Refresh
        </Button>
      </div>
    </div>
  )
}

function NotificationContent({ notification }: { notification: NotificationMessage }) {
  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 mt-0.5">
        {getNotificationIcon(notification.type)}
      </div>
      <div className="flex-1 space-y-1">
        <div className="flex items-start justify-between">
          <p className="text-sm font-medium">{notification.title}</p>
          {!notification.read && (
            <div className="h-2 w-2 rounded-full bg-primary flex-shrink-0 ml-2 mt-1" />
          )}
        </div>
        <p className="text-sm text-muted-foreground line-clamp-2">
          {notification.message}
        </p>
        <p className="text-xs text-muted-foreground">
          {getTimeAgo(notification.timestamp)}
        </p>
      </div>
    </div>
  )
}
