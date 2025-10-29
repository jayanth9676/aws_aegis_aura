'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Shield, AlertTriangle, Phone, Eye, Clock, Ban } from 'lucide-react'

const fraudTips = [
  {
    icon: AlertTriangle,
    title: 'Be wary of pressure',
    description: 'Scammers create urgency to prevent you from thinking clearly. Take your time to verify all payment details.',
    color: 'text-warning',
  },
  {
    icon: Eye,
    title: 'Verify payee details',
    description: 'Always double-check account numbers and sort codes, especially for new payees or large amounts.',
    color: 'text-info',
  },
  {
    icon: Ban,
    title: "Don't share security details",
    description: 'Never share your PIN, password, or one-time codes. We will never ask for these.',
    color: 'text-destructive',
  },
  {
    icon: Phone,
    title: 'Contact us if unsure',
    description: 'If anything feels wrong or you're uncertain, stop and contact us immediately on 0800-123-4567.',
    color: 'text-success',
  },
]

const commonScams = [
  {
    title: 'Investment Scams',
    description: 'Fraudsters promise high returns on fake investments, often using pressure tactics and fake websites.',
    redFlags: [
      'Promises of guaranteed high returns',
      'Pressure to invest quickly',
      'Unregulated investment firms',
      'Celebrity endorsements',
    ],
  },
  {
    title: 'Romance Scams',
    description: 'Criminals build fake relationships online and then ask for money for emergencies or travel.',
    redFlags: [
      'Quick declarations of love',
      'Never meeting in person',
      'Requests for money transfers',
      'Sob stories and emergencies',
    ],
  },
  {
    title: 'Impersonation Scams',
    description: 'Scammers pretend to be from your bank, police, or other trusted organizations.',
    redFlags: [
      'Unexpected calls about your account',
      'Requests to move money to "safe" accounts',
      'Threats or urgent demands',
      'Requests for passwords or PINs',
    ],
  },
]

export function ScamEducation() {
  return (
    <div className="space-y-6">
      {/* Quick Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Fraud Prevention Tips
          </CardTitle>
          <CardDescription>Stay safe from scams</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {fraudTips.map((tip, index) => (
              <div key={index} className="flex items-start gap-3">
                <div className={`${tip.color} mt-1`}>
                  <tip.icon className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm mb-1">{tip.title}</h3>
                  <p className="text-sm text-muted-foreground">{tip.description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Common Scams */}
      <Card>
        <CardHeader>
          <CardTitle>Common Scam Types</CardTitle>
          <CardDescription>Learn to recognize fraud attempts</CardDescription>
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible className="w-full">
            {commonScams.map((scam, index) => (
              <AccordionItem key={index} value={`scam-${index}`}>
                <AccordionTrigger>{scam.title}</AccordionTrigger>
                <AccordionContent>
                  <p className="mb-4">{scam.description}</p>
                  <div>
                    <p className="font-semibold text-sm mb-2">Red Flags:</p>
                    <ul className="space-y-1">
                      {scam.redFlags.map((flag, i) => (
                        <li key={i} className="text-sm text-muted-foreground flex items-center gap-2">
                          <div className="h-1.5 w-1.5 rounded-full bg-destructive flex-shrink-0" />
                          {flag}
                        </li>
                      ))}
                    </ul>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </CardContent>
      </Card>

      {/* Emergency Contact */}
      <Alert>
        <Phone className="h-4 w-4" />
        <AlertDescription>
          <strong>Suspicious activity?</strong> Call us immediately on{' '}
          <strong className="text-foreground">0800-123-4567</strong> (24/7) or report online at aegis.com/report
        </AlertDescription>
      </Alert>
    </div>
  )
}

