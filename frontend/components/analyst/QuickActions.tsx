'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  MessageSquare,
  BarChart3,
  FileDown,
  Settings,
  PlusCircle,
  Search,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface QuickAction {
  title: string
  description: string
  icon: React.ElementType
  href: string
  variant?: 'default' | 'outline' | 'secondary'
  badge?: number
}

const actions: QuickAction[] = [
  {
    title: 'New Investigation',
    description: 'Start a manual case investigation',
    icon: PlusCircle,
    href: '/analyst/cases/new',
    variant: 'default',
  },
  {
    title: 'AI Co-pilot',
    description: 'Ask questions about cases and patterns',
    icon: MessageSquare,
    href: '/analyst/copilot',
    variant: 'outline',
  },
  {
    title: 'Analytics',
    description: 'View fraud trends and model performance',
    icon: BarChart3,
    href: '/analyst/dashboard',
    variant: 'outline',
  },
  {
    title: 'Search Cases',
    description: 'Advanced case search and filters',
    icon: Search,
    href: '/analyst/cases',
    variant: 'outline',
  },
  {
    title: 'Export Report',
    description: 'Generate and download reports',
    icon: FileDown,
    href: '/analyst/reports',
    variant: 'secondary',
  },
  {
    title: 'Settings',
    description: 'Configure alerts and preferences',
    icon: Settings,
    href: '/analyst/settings',
    variant: 'secondary',
  },
]

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
        <CardDescription>Common tasks and shortcuts</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {actions.map((action, index) => (
            <Link key={index} href={action.href}>
              <Button
                variant={action.variant || 'outline'}
                className="w-full h-auto flex-col items-start p-4 gap-2"
              >
                <div className="flex items-center justify-between w-full">
                  <action.icon className="h-5 w-5" />
                  {action.badge !== undefined && (
                    <Badge variant="secondary" className="ml-auto">
                      {action.badge}
                    </Badge>
                  )}
                </div>
                <div className="text-left space-y-1">
                  <p className="font-semibold text-sm">{action.title}</p>
                  <p className="text-xs text-muted-foreground font-normal">
                    {action.description}
                  </p>
                </div>
              </Button>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

