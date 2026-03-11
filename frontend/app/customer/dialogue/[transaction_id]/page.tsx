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
import { apiClient } from '@/lib/api-client'

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
  const [streamingMessage, setStreamingMessage] = useState<string | null>(null)
  const totalSteps = 3

  const handleResponse = async (response: string) => {
    // Add user message
    const userMessage: AgentMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: response,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Call backend API for AI response
    try {
      setStreamingMessage('Analyzing your response...')
      
      const result = await apiClient.customerDialogue(
        params.transaction_id, 
        response,
        messages.map(m => ({ role: m.role, message: m.content }))
      )

      setStreamingMessage(null)
      setStep((s) => s + 1)

      const fullResponseText = result.message || 'I am processing your response.'
      
      // Use questions/education_tip/action to structure suggestions naturally
      let nextSuggestions = result.questions || []
      
      // Build final text including education tip if present
      let finalContent = fullResponseText
      if (result.education_tip) {
        finalContent += `\n\n💡 **Security Tip:** ${result.education_tip}`
      }
      
      // Default suggestions if none provided
      if (nextSuggestions.length === 0) {
        if (result.recommended_action === 'CANCEL') {
          nextSuggestions = ['Cancel this payment']
        } else if (result.recommended_action === 'VERIFY') {
          nextSuggestions = ['Proceed safely']
        }
      }

      const aiMessage: AgentMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: finalContent,
        timestamp: new Date().toISOString(),
        agent_name: 'Aegis Security',
        suggestions: nextSuggestions,
      }
      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error("Dialogue agent error:", error)
      setStreamingMessage(null)
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I am having trouble connecting to the Aegis network right now.',
        timestamp: new Date().toISOString(),
        agent_name: 'System',
      }])
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
        <Card className="h-[600px] flex flex-col shadow-lg border-2">
          <CustomerChat 
            messages={messages} 
            streamingMessage={streamingMessage}
            onResponse={handleResponse} 
          />
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
