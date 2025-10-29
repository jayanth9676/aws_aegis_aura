'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { CustomerChat } from '@/components/customer/CustomerChat'
import { ArrowLeft, Shield, AlertTriangle } from 'lucide-react'
import Link from 'next/link'
import type { AgentMessage } from '@/types'

interface DialoguePageProps {
  params: { transaction_id: string }
}

export default function DialoguePage({ params }: DialoguePageProps) {
  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: `⚠️ We've detected unusual activity with this payment.\n\nBefore you proceed, we need to verify some details to protect you from potential fraud.\n\nThis payment is to: "Unknown Ltd" for £8,500\n\nAre you expecting to make this payment?`,
      timestamp: new Date().toISOString(),
      agent_name: 'Aegis Security',
      suggestions: ['Yes, I am expecting this payment', 'No, I did not authorize this'],
    },
  ])

  const [step, setStep] = useState(1)
  const totalSteps = 3

  const handleResponse = (response: string) => {
    // Add user message
    const userMessage: AgentMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: response,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: AgentMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getNextQuestion(step, response),
        timestamp: new Date().toISOString(),
        agent_name: 'Aegis Security',
        suggestions: getNextSuggestions(step),
      }
      setMessages((prev) => [...prev, aiMessage])
      setStep((s) => s + 1)
    }, 1000)
  }

  const getNextQuestion = (currentStep: number, lastResponse: string): string => {
    if (lastResponse.includes('not authorize')) {
      return `Thank you for confirming. We've blocked this payment immediately.\n\nYour account is safe. We'll investigate this and contact you shortly.\n\nWhat would you like to do next?`
    }

    switch (currentStep) {
      case 1:
        return `Thank you. To verify this is legitimate:\n\nAre you currently on a phone call with someone asking you to make this payment?`
      case 2:
        return `⚠️ This is a common scam tactic. Fraudsters often stay on the phone to prevent you from thinking clearly.\n\nWe strongly recommend canceling this payment and contacting the recipient through official channels.\n\nWhat would you like to do?`
      default:
        return 'Thank you for your responses. Your security is our priority.'
    }
  }

  const getNextSuggestions = (currentStep: number): string[] => {
    switch (currentStep) {
      case 1:
        return ['Yes, I am on a call', 'No, I am not on a call']
      case 2:
        return ['Cancel this payment', 'Proceed anyway', 'Speak to an advisor']
      default:
        return []
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/customer">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              <span className="font-semibold">Secure Verification</span>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 max-w-5xl">
        {/* Progress */}
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Verification Progress</span>
              <Badge variant="outline">
                Step {step} of {totalSteps}
              </Badge>
            </div>
            <Progress value={(step / totalSteps) * 100} className="h-2" />
          </CardHeader>
        </Card>

        {/* Warning Alert */}
        <div className="mb-6 p-4 bg-warning/10 border-2 border-warning rounded-lg flex items-start gap-3">
          <AlertTriangle className="h-6 w-6 text-warning mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-semibold text-warning mb-1">High Risk Transaction Detected</p>
            <p className="text-sm text-muted-foreground">
              Please answer these security questions carefully. If anything feels wrong, stop and contact us.
            </p>
          </div>
        </div>

        {/* Chat Interface */}
        <Card className="h-[600px] flex flex-col">
          <CustomerChat messages={messages} onResponse={handleResponse} />
        </Card>

        {/* Emergency Contact */}
        <div className="mt-6 text-center">
          <p className="text-sm text-muted-foreground">
            Need immediate help?{' '}
            <Button variant="link" className="px-1 font-semibold">
              Call 0800-123-4567
            </Button>
          </p>
        </div>
      </div>
    </div>
  )
}
