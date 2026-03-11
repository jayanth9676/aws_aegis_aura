'use client'

import { useState } from 'react'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { SystemCopilotDrawer } from '../copilot/SystemCopilotDrawer'
import { cn } from '@/lib/utils'
import { usePathname } from 'next/navigation'

interface MainLayoutProps {
  children: React.ReactNode
  className?: string
}

export function MainLayout({ children, className }: MainLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const pathname = usePathname()
  const isAnalystRoute = pathname?.startsWith('/analyst')

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Desktop Sidebar */}
      {isAnalystRoute && (
        <div className="hidden lg:block">
          <Sidebar collapsed={sidebarCollapsed} />
        </div>
      )}

      {/* Mobile Sidebar Overlay */}
      {isAnalystRoute && mobileSidebarOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 z-50 lg:hidden">
            <Sidebar />
          </div>
        </>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {isAnalystRoute && (
          <Header
            onMenuClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
            showMenuButton={true}
          />
        )}

        {/* Content */}
        <main className={cn('flex-1 overflow-y-auto bg-muted/30', className)}>
          {children}
        </main>

        {/* Global Copilot Drawer */}
        {isAnalystRoute && <SystemCopilotDrawer />}
      </div>
    </div>
  )
}

