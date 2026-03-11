'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Shield,
  LayoutDashboard,
  FileText,
  MessageSquare,
  BarChart3,
  Settings,
  Users,
  Bell,
  Activity,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'

interface NavItem {
  title: string
  href: string
  icon: React.ElementType
  badge?: number
}

const analystNavItems: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/analyst',
    icon: LayoutDashboard,
  },
  {
    title: 'Agent Core',
    href: '/analyst/agents',
    icon: Activity,
  },
  {
    title: 'Simulator',
    href: '/analyst/simulator',
    icon: FileText,
  },
  {
    title: 'Cases',
    href: '/analyst/cases',
    icon: FileText,
  },
  {
    title: 'AI Co-pilot',
    href: '/analyst/copilot',
    icon: MessageSquare,
  },
  {
    title: 'Analytics',
    href: '/analyst/dashboard',
    icon: BarChart3,
  },
  {
    title: 'Activity Log',
    href: '/analyst/activity',
    icon: Activity,
  },
]

const adminNavItems: NavItem[] = [
  {
    title: 'Team',
    href: '/analyst/team',
    icon: Users,
  },
  {
    title: 'Notifications',
    href: '/analyst/notifications',
    icon: Bell,
  },
  {
    title: 'Settings',
    href: '/analyst/settings',
    icon: Settings,
  },
]

interface SidebarProps {
  className?: string
  collapsed?: boolean
}

export function Sidebar({ className, collapsed = false }: SidebarProps) {
  const pathname = usePathname()

  return (
    <div
      className={cn(
        'flex h-screen flex-col border-r bg-background transition-all duration-300',
        collapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/" className="flex items-center space-x-2">
          <Shield className="h-6 w-6 text-primary" />
          {!collapsed && (
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
              AEGIS
            </span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3 py-4">
        {/* Main Navigation */}
        <div className="space-y-1">
          {analystNavItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
                title={collapsed ? item.title : undefined}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {!collapsed && (
                  <>
                    <span className="flex-1">{item.title}</span>
                    {item.badge !== undefined && (
                      <Badge variant="secondary" className="ml-auto">
                        {item.badge}
                      </Badge>
                    )}
                  </>
                )}
              </Link>
            )
          })}
        </div>

        {/* Divider */}
        {!collapsed && <div className="my-4 border-t" />}

        {/* Admin Navigation */}
        <div className="space-y-1 mt-4">
          {adminNavItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
                title={collapsed ? item.title : undefined}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {!collapsed && <span className="flex-1">{item.title}</span>}
              </Link>
            )
          })}
        </div>
      </ScrollArea>

      {/* System Status */}
      {!collapsed && (
        <div className="border-t p-4">
          <div className="flex items-center space-x-2 rounded-lg bg-success-light p-3">
            <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
            <span className="text-xs font-medium text-success-foreground">
              All Systems Operational
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

