/**
 * API Client for Aegis Fraud Prevention Platform
 * Handles all backend API communication with retry logic and error handling
 */

import type {
  Case,
  CaseQuery,
  CaseActionForm,
  DashboardStats,
  Transaction,
  Customer,
  AgentMessage,
  APIResponse,
  PaginatedResponse,
  NetworkGraphData,
  SHAPExplanation,
  FraudTrendData,
  AnalystPerformance,
  ModelMetrics,
} from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const MAX_RETRIES = 3
const RETRY_DELAY = 1000

class ApiClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  private async sleep(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  private async request<T = any>(
    endpoint: string,
    options?: RequestInit,
    retries = 0
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      })

      if (!response.ok) {
        // Handle different error status codes
        if (response.status === 401) {
          throw new Error('Unauthorized. Please log in.')
        }
        if (response.status === 403) {
          throw new Error('Forbidden. You do not have permission.')
        }
        if (response.status === 404) {
          throw new Error('Resource not found.')
        }
        if (response.status >= 500 && retries < MAX_RETRIES) {
          // Retry on server errors
          await this.sleep(RETRY_DELAY * Math.pow(2, retries))
          return this.request<T>(endpoint, options, retries + 1)
        }

        const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(error.detail || `API Error: ${response.status}`)
      }

      return response.json()
    } catch (error) {
      if (error instanceof TypeError && retries < MAX_RETRIES) {
        // Network error, retry
        await this.sleep(RETRY_DELAY * Math.pow(2, retries))
        return this.request<T>(endpoint, options, retries + 1)
      }
      throw error
    }
  }

  async get<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' })
  }

  async post<T = any>(endpoint: string, data: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async patch<T = any>(endpoint: string, data: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  async put<T = any>(endpoint: string, data: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async delete<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' })
  }

  // Health Check
  async healthCheck() {
    return this.get('/health')
  }

  // Transaction API
  async submitTransaction(transaction: any): Promise<Transaction> {
    return this.post<Transaction>('/api/v1/transactions/submit', transaction)
  }

  async getTransactions(query?: {
    customer_id?: string
    status?: string
    date_from?: string
    date_to?: string
    page?: number
    page_size?: number
  }): Promise<PaginatedResponse<Transaction>> {
    const params = new URLSearchParams()
    if (query) {
      Object.entries(query).forEach(([key, value]) => {
        if (value !== undefined) params.append(key, value.toString())
      })
    }
    const queryString = params.toString()
    return this.get<PaginatedResponse<Transaction>>(
      `/api/v1/transactions${queryString ? `?${queryString}` : ''}`
    )
  }

  async getTransaction(transactionId: string): Promise<Transaction> {
    return this.get<Transaction>(`/api/v1/transactions/${transactionId}`)
  }

  // Cases API
  async getCases(query?: CaseQuery): Promise<PaginatedResponse<Case>> {
    const params = new URLSearchParams()
    if (query) {
      if (query.filters?.status) {
        query.filters.status.forEach(s => params.append('status', s))
      }
      if (query.filters?.risk_level) {
        query.filters.risk_level.forEach(r => params.append('risk_level', r))
      }
      if (query.filters?.assigned_analyst) {
        params.append('assigned_analyst', query.filters.assigned_analyst)
      }
      if (query.filters?.date_from) {
        params.append('date_from', query.filters.date_from)
      }
      if (query.filters?.date_to) {
        params.append('date_to', query.filters.date_to)
      }
      if (query.filters?.search) {
        params.append('search', query.filters.search)
      }
      if (query.sort_by) {
        params.append('sort_by', query.sort_by)
      }
      if (query.sort_order) {
        params.append('sort_order', query.sort_order)
      }
      if (query.page) {
        params.append('page', query.page.toString())
      }
      if (query.page_size) {
        params.append('page_size', query.page_size.toString())
      }
    }
    const queryString = params.toString()
    return this.get<PaginatedResponse<Case>>(
      `/api/v1/cases${queryString ? `?${queryString}` : ''}`
    )
  }

  async getCase(caseId: string): Promise<Case> {
    return this.get<Case>(`/api/v1/cases/${caseId}`)
  }

  async updateCase(caseId: string, updates: Partial<Case>): Promise<Case> {
    return this.patch<Case>(`/api/v1/cases/${caseId}`, updates)
  }

  async caseAction(caseId: string, action: CaseActionForm): Promise<Case> {
    return this.post<Case>(`/api/v1/cases/${caseId}/action`, action)
  }

  async assignCase(caseId: string, analystId: string): Promise<Case> {
    return this.post<Case>(`/api/v1/cases/${caseId}/assign`, { analyst_id: analystId })
  }

  async escalateCase(caseId: string, reason: string): Promise<Case> {
    return this.post<Case>(`/api/v1/cases/${caseId}/escalate`, { reason })
  }

  async closeCase(caseId: string, notes?: string): Promise<Case> {
    return this.post<Case>(`/api/v1/cases/${caseId}/close`, { notes })
  }

  async getCaseNetworkGraph(caseId: string): Promise<NetworkGraphData> {
    return this.get<NetworkGraphData>(`/api/v1/cases/${caseId}/network`)
  }

  async getCaseSHAPExplanation(caseId: string): Promise<SHAPExplanation> {
    return this.get<SHAPExplanation>(`/api/v1/cases/${caseId}/shap`)
  }

  // Customer API
  async getCustomer(customerId: string): Promise<Customer> {
    return this.get<Customer>(`/api/v1/customers/${customerId}`)
  }

  async getCustomerTransactions(customerId: string): Promise<Transaction[]> {
    return this.get<Transaction[]>(`/api/v1/customers/${customerId}/transactions`)
  }

  async getCustomerCases(customerId: string): Promise<Case[]> {
    return this.get<Case[]>(`/api/v1/customers/${customerId}/cases`)
  }

  // Dashboard API
  async getDashboardStats(): Promise<DashboardStats> {
    return this.get<DashboardStats>('/api/v1/dashboard/stats')
  }

  async getFraudTrends(days: number = 30): Promise<FraudTrendData[]> {
    return this.get<FraudTrendData[]>(`/api/v1/dashboard/trends?days=${days}`)
  }

  async getAnalystPerformance(): Promise<AnalystPerformance[]> {
    return this.get<AnalystPerformance[]>('/api/v1/dashboard/analyst-performance')
  }

  async getModelMetrics(): Promise<ModelMetrics> {
    return this.get<ModelMetrics>('/api/v1/dashboard/model-metrics')
  }

  // Copilot API
  async copilotQuery(query: string, context?: any): Promise<AgentMessage> {
    return this.post<AgentMessage>('/api/v1/copilot/query', { query, context })
  }

  async copilotChat(messages: AgentMessage[]): Promise<AgentMessage> {
    return this.post<AgentMessage>('/api/v1/copilot/chat', { messages })
  }

  // Customer Dialogue API
  async customerDialogue(transactionId: string, message: string): Promise<AgentMessage> {
    return this.post<AgentMessage>('/api/v1/dialogue/customer', { 
      transaction_id: transactionId, 
      message 
    })
  }

  async getDialogueHistory(transactionId: string): Promise<AgentMessage[]> {
    return this.get<AgentMessage[]>(`/api/v1/dialogue/customer/${transactionId}/history`)
  }

  // Agent API
  async getAgents(): Promise<any[]> {
    return this.get<any[]>('/api/v1/agents')
  }

  async getAgentStatus(agentName: string): Promise<any> {
    return this.get<any>(`/api/v1/agents/${agentName}/status`)
  }

  // Notifications API
  async getNotifications(unread_only: boolean = false): Promise<any[]> {
    return this.get<any[]>(`/api/v1/notifications${unread_only ? '?unread_only=true' : ''}`)
  }

  async markNotificationRead(notificationId: string): Promise<void> {
    return this.post<void>(`/api/v1/notifications/${notificationId}/read`, {})
  }

  async markAllNotificationsRead(): Promise<void> {
    return this.post<void>('/api/v1/notifications/read-all', {})
  }
}

export const apiClient = new ApiClient(API_BASE_URL)

