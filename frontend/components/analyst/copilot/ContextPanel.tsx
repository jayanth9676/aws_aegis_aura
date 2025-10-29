'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { FileText, Users, Lightbulb, Clock } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'

interface ContextPanelProps {
  currentCase?: {
    case_id: string
    risk_score: number
    status: string
  }
}

const recentCases = [
  { id: 'CASE-1240', risk: 92, similarity: 0.87, reason: 'Similar payee patterns' },
  { id: 'CASE-1235', risk: 88, similarity: 0.82, reason: 'Active call detected' },
  { id: 'CASE-1230', risk: 85, similarity: 0.79, reason: 'Behavioral anomalies' },
]

const knowledgeBase = [
  { title: 'Investment Scam Typology', relevance: 0.91 },
  { title: 'Romance Scam Indicators', relevance: 0.85 },
  { title: 'Invoice Fraud Detection', relevance: 0.78 },
]

const suggestions = [
  "What are the key risk factors for this transaction?",
  "Compare this case to historical patterns",
  "What fraud typology does this match?",
  "What additional verification is needed?",
]

export function ContextPanel({ currentCase }: ContextPanelProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-lg">Context & Insights</CardTitle>
        <CardDescription>Relevant information for analysis</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="suggestions" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="suggestions">
              <Lightbulb className="h-4 w-4 mr-1" />
              <span className="hidden sm:inline">Suggestions</span>
            </TabsTrigger>
            <TabsTrigger value="similar">
              <Users className="h-4 w-4 mr-1" />
              <span className="hidden sm:inline">Similar</span>
            </TabsTrigger>
            <TabsTrigger value="docs">
              <FileText className="h-4 w-4 mr-1" />
              <span className="hidden sm:inline">Docs</span>
            </TabsTrigger>
          </TabsList>

          <ScrollArea className="h-[600px] mt-4">
            <TabsContent value="suggestions" className="space-y-2">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                >
                  <p className="text-sm">{suggestion}</p>
                </div>
              ))}
            </TabsContent>

            <TabsContent value="similar" className="space-y-3">
              {recentCases.map((case_) => (
                <Card key={case_.id} className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">{case_.id}</span>
                      <Badge variant={case_.risk >= 85 ? 'destructive' : 'default'}>
                        Risk: {case_.risk}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mb-1">
                      Similarity: {(case_.similarity * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-muted-foreground">{case_.reason}</p>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>

            <TabsContent value="docs" className="space-y-3">
              {knowledgeBase.map((doc, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm font-medium mb-1">{doc.title}</p>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-muted rounded-full h-1.5">
                            <div
                              className="bg-primary h-1.5 rounded-full"
                              style={{ width: `${doc.relevance * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {(doc.relevance * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
          </ScrollArea>
        </Tabs>
      </CardContent>
    </Card>
  )
}

