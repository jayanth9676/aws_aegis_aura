import { MainLayout } from '@/components/layout/MainLayout'
import { Shield, TrendingUp, Users, Activity, Database, Zap, Lock, Eye, Brain, Network, ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Link from 'next/link'

export default function Home() {
  return (
    <MainLayout>
      {/* Hero Section with Gradient */}
      <section className="relative overflow-hidden">
        {/* Animated background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 opacity-60" />
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
          <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
          <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-pink-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />
        </div>

        <div className="relative container mx-auto px-4 py-24 md:py-32">
          <div className="flex flex-col items-center text-center space-y-8">
            {/* Badge */}
            <Badge variant="secondary" className="px-6 py-3 text-base backdrop-blur-sm bg-white/50 border-2 border-white/60 shadow-lg">
              <Sparkles className="w-4 h-4 mr-2 inline-block text-purple-500" />
              Powered by AWS Bedrock AgentCore Runtime
            </Badge>
            
            {/* Title with Gradient */}
            <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight">
              <span className="gradient-text">
                AEGIS
              </span>
            </h1>
            
            <p className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
              Agentic AI Fraud Prevention
            </p>
            
            <p className="text-xl md:text-2xl text-gray-600 max-w-4xl leading-relaxed">
              Multi-agent AI system for APP scam detection with real-time ML predictions, 
              behavioral analysis, and graph-based network intelligence
            </p>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 mt-8">
              <Link href="/analyst">
                <Button size="lg" className="btn-shiny bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-6 text-lg shadow-xl hover:shadow-2xl transition-all">
                  <Users className="w-6 h-6 mr-2" />
                  Analyst Dashboard
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link href="/customer">
                <Button size="lg" variant="outline" className="border-2 backdrop-blur-sm bg-white/50 hover:bg-white/80 px-8 py-6 text-lg shadow-lg">
                  <Activity className="w-6 h-6 mr-2" />
                  Customer Portal
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* System Status - Glass Morphism */}
      <section className="container mx-auto px-4 py-12">
        <Card className="card-premium border-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-3 text-2xl">
                  <div className="relative">
                    <div className="w-4 h-4 bg-green-500 rounded-full animate-pulse" />
                    <div className="absolute inset-0 w-4 h-4 bg-green-500 rounded-full animate-ping opacity-75" />
                  </div>
                  System Status
                </CardTitle>
                <CardDescription className="text-base mt-1">All systems operational · Real-time monitoring active</CardDescription>
              </div>
              <Badge className="bg-green-100 text-green-700 border-green-200 px-4 py-2 text-sm">
                <CheckCircle2 className="w-4 h-4 mr-2" />
                99.9% Uptime
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="flex items-center space-x-4 p-4 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100/50">
                <div className="p-3 bg-blue-500 rounded-lg shadow-lg">
                  <Shield className="w-7 h-7 text-white" />
                </div>
                <div>
                  <p className="font-bold text-xl text-gray-900">13 Agents Active</p>
                  <p className="text-sm text-gray-600">AgentCore Runtime</p>
                </div>
              </div>
              <div className="flex items-center space-x-4 p-4 rounded-xl bg-gradient-to-br from-green-50 to-green-100/50">
                <div className="p-3 bg-green-500 rounded-lg shadow-lg">
                  <Database className="w-7 h-7 text-white" />
                </div>
                <div>
                  <p className="font-bold text-xl text-gray-900">Neo4j Connected</p>
                  <p className="text-sm text-gray-600">Graph Database</p>
                </div>
              </div>
              <div className="flex items-center space-x-4 p-4 rounded-xl bg-gradient-to-br from-amber-50 to-amber-100/50">
                <div className="p-3 bg-amber-500 rounded-lg shadow-lg">
                  <Zap className="w-7 h-7 text-white" />
                </div>
                <div>
                  <p className="font-bold text-xl text-gray-900">&lt;500ms Response</p>
                  <p className="text-sm text-gray-600">95th Percentile</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Platform <span className="gradient-text">Capabilities</span>
          </h2>
          <p className="text-xl text-gray-600">Enterprise-grade fraud detection powered by cutting-edge AI</p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Agent System */}
          <Card className="card-premium group hover:scale-105 transition-all duration-300">
            <CardHeader>
              <div className="p-4 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl w-fit mb-4 shadow-lg group-hover:shadow-xl transition-shadow">
                <Brain className="w-10 h-10 text-white" />
              </div>
              <CardTitle className="text-2xl">13 Specialized Agents</CardTitle>
              <CardDescription className="text-base">Multi-agent orchestration system</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Supervisor Orchestration</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">5 Context Agents</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">2 Analysis Agents</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">5 Decision Agents</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* ML Detection */}
          <Card className="card-premium group hover:scale-105 transition-all duration-300">
            <CardHeader>
              <div className="p-4 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl w-fit mb-4 shadow-lg group-hover:shadow-xl transition-shadow">
                <TrendingUp className="w-10 h-10 text-white" />
              </div>
              <CardTitle className="text-2xl">Advanced ML Detection</CardTitle>
              <CardDescription className="text-base">AUC &gt;0.95 accuracy</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Ensemble ML Models</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Behavioral Analysis</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">SHAP Explainability</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Real-time Scoring</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Graph Analysis */}
          <Card className="card-premium group hover:scale-105 transition-all duration-300">
            <CardHeader>
              <div className="p-4 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl w-fit mb-4 shadow-lg group-hover:shadow-xl transition-shadow">
                <Network className="w-10 h-10 text-white" />
              </div>
              <CardTitle className="text-2xl">Graph Intelligence</CardTitle>
              <CardDescription className="text-base">Network analysis powered by Neo4j</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Mule Account Detection</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Relationship Mapping</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Path Analysis</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Pattern Detection</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Real-time Response */}
          <Card className="card-premium group hover:scale-105 transition-all duration-300">
            <CardHeader>
              <div className="p-4 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl w-fit mb-4 shadow-lg group-hover:shadow-xl transition-shadow">
                <Zap className="w-10 h-10 text-white" />
              </div>
              <CardTitle className="text-2xl">Real-time Response</CardTitle>
              <CardDescription className="text-base">&lt;500ms latency</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Instant Decisions</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Conversational AI</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Streaming Responses</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Live Dashboard</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Security & Compliance */}
          <Card className="card-premium group hover:scale-105 transition-all duration-300">
            <CardHeader>
              <div className="p-4 bg-gradient-to-br from-red-500 to-rose-600 rounded-2xl w-fit mb-4 shadow-lg group-hover:shadow-xl transition-shadow">
                <Lock className="w-10 h-10 text-white" />
              </div>
              <CardTitle className="text-2xl">Security & Compliance</CardTitle>
              <CardDescription className="text-base">Enterprise-grade protection</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Bedrock Guardrails</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Cognito Authentication</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">7-Year Audit Trail</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">PSR UK Compliance</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Observability */}
          <Card className="card-premium group hover:scale-105 transition-all duration-300">
            <CardHeader>
              <div className="p-4 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-2xl w-fit mb-4 shadow-lg group-hover:shadow-xl transition-shadow">
                <Eye className="w-10 h-10 text-white" />
              </div>
              <CardTitle className="text-2xl">Full Observability</CardTitle>
              <CardDescription className="text-base">Complete system insights</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Distributed Tracing</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Performance Metrics</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Bias Detection</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Automated Alerting</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <Card className="card-premium bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 border-0">
          <CardContent className="p-12 text-center">
            <h2 className="text-4xl md:text-5xl font-bold text-black mb-6">
              Ready to Prevent Fraud?
            </h2>
            <p className="text-xl text-black/90 mb-8 max-w-2xl mx-auto">
              Join the next generation of fraud prevention with AI-powered protection
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/analyst">
                <Button size="lg" className="bg-white text-purple-600 hover:bg-gray-100 px-8 py-6 text-lg shadow-xl">
                  Get Started
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link href="/customer">
                <Button size="lg" variant="outline" className="border-2 border-white text-black hover:bg-white/10 px-8 py-6 text-lg">
                  Learn More
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </section>
    </MainLayout>
  )
}

/* Add these animations to your tailwind.config.ts */
