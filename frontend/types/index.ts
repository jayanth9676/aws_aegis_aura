// Core Types for Aegis Fraud Prevention Platform

// Case Types
export type CaseStatus =
  | 'NEW'
  | 'INVESTIGATING'
  | 'PENDING_DECISION'
  | 'APPROVED'
  | 'BLOCKED'
  | 'ESCALATED'
  | 'RESOLVED'
  | 'CLOSED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Case {
  id: string;
  case_id: string;
  transaction_id: string;
  customer_id: string;
  status: CaseStatus;
  risk_score: number;
  confidence: number;
  assigned_analyst?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  timeline: TimelineEvent[];
  evidence: Evidence[];
  decision?: CaseDecision;
  network_data?: NetworkNode[];
  agent_reasoning?: AgentReasoning[];
  fraud_typology?: string;
  shap_values?: SHAPValue[];
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  type: 'TRANSACTION' | 'AGENT_ANALYSIS' | 'ANALYST_ACTION' | 'CUSTOMER_RESPONSE' | 'SYSTEM_DECISION';
  description: string;
  agent?: string;
  data?: Record<string, any>;
  risk_impact?: number;
}

export interface Evidence {
  id: string;
  type: string;
  source: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  timestamp: string;
  data?: Record<string, any>;
}

export interface CaseDecision {
  action: 'ALLOW' | 'CHALLENGE' | 'BLOCK' | 'ESCALATE';
  reason: string;
  reason_codes: string[];
  analyst_notes?: string;
  decided_by: string;
  decided_at: string;
  confidence: number;
}

// Transaction Types
export type TransactionStatus =
  | 'PENDING'
  | 'APPROVED'
  | 'BLOCKED'
  | 'CHALLENGED'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export interface Transaction {
  id: string;
  transaction_id: string;
  customer_id: string;
  amount: number;
  currency: string;
  payee_name: string;
  payee_account: string;
  payee_sort_code?: string;
  timestamp: string;
  status: TransactionStatus;
  risk_score?: number;
  channel: 'WEB' | 'MOBILE' | 'BRANCH' | 'PHONE';
  payment_method: 'FASTER_PAYMENT' | 'BACS' | 'CHAPS' | 'SEPA';
  behavioral_signals?: BehavioralSignals;
  device_info?: DeviceInfo;
}

export interface BehavioralSignals {
  typing_speed: number;
  mouse_movement: number[];
  navigation_pattern: string[];
  device_fingerprint: string;
  active_call: boolean;
  hesitation_score: number;
  session_duration: number;
  anomaly_score?: number;
}

export interface DeviceInfo {
  device_id: string;
  device_type: 'DESKTOP' | 'MOBILE' | 'TABLET';
  os: string;
  browser: string;
  ip_address: string;
  location?: {
    country: string;
    city: string;
    coordinates?: [number, number];
  };
}

// Customer Types
export interface Customer {
  id: string;
  customer_id: string;
  name: string;
  email?: string;
  phone?: string;
  date_of_birth?: string;
  account_created: string;
  kyc_status: 'VERIFIED' | 'PENDING' | 'FAILED';
  vulnerability_score?: number;
  risk_profile: 'LOW' | 'MEDIUM' | 'HIGH';
  previous_fraud: boolean;
  lifetime_transactions: number;
  average_transaction_value: number;
}

// Payee Types
export interface Payee {
  payee_account: string;
  payee_name: string;
  payee_sort_code?: string;
  bank_name?: string;
  verification_status: 'VERIFIED' | 'MISMATCH' | 'UNKNOWN';
  watchlist_hit: boolean;
  sanctions_hit: boolean;
  first_seen: string;
  transaction_count: number;
  total_received: number;
}

// Agent Types
export interface AgentMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  agent_name?: string;
  confidence?: number;
  suggestions?: string[];
  reasoning?: string;
}

export interface AgentReasoning {
  agent_name: string;
  agent_type: 'CONTEXT' | 'ANALYSIS' | 'DECISION';
  execution_time_ms: number;
  findings: string[];
  risk_contribution: number;
  confidence: number;
  raw_data?: Record<string, any>;
  timestamp: string;
}

// Network Graph Types
export interface NetworkNode {
  id: string;
  type: 'CUSTOMER' | 'ACCOUNT' | 'PAYEE' | 'MULE';
  label: string;
  risk_score?: number;
  properties?: Record<string, any>;
}

export interface NetworkEdge {
  source: string;
  target: string;
  type: 'TRANSACTION' | 'OWNS' | 'LINKED_TO';
  amount?: number;
  timestamp?: string;
  properties?: Record<string, any>;
}

export interface NetworkGraphData {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  mule_probability?: number;
  network_centrality?: number;
}

// SHAP Explanation Types
export interface SHAPValue {
  feature_name: string;
  feature_value: any;
  shap_value: number;
  contribution: 'POSITIVE' | 'NEGATIVE';
  importance_rank: number;
}

export interface SHAPExplanation {
  prediction: number;
  base_value: number;
  shap_values: SHAPValue[];
  model_name: string;
  model_version: string;
}

// Dashboard Statistics Types
export interface DashboardStats {
  active_cases: number;
  high_risk_cases: number;
  resolved_today: number;
  total_cases: number;
  avg_risk_score: number;
  fraud_detection_rate: number;
  false_positive_rate: number;
  transactions_today: number;
  blocked_transactions_today: number;
}

// Analytics Types
export interface FraudTrendData {
  date: string;
  fraud_count: number;
  total_transactions: number;
  fraud_rate: number;
}

export interface RiskDistributionData {
  risk_bin: string;
  count: number;
  percentage: number;
}

export interface FraudTypologyData {
  typology: string;
  count: number;
  percentage: number;
  color: string;
}

export interface AnalystPerformance {
  analyst_id: string;
  analyst_name: string;
  cases_handled: number;
  avg_resolution_time_minutes: number;
  accuracy_rate: number;
  false_positive_rate: number;
}

export interface ModelMetrics {
  model_name: string;
  model_version: string;
  auc: number;
  precision: number;
  recall: number;
  f1_score: number;
  last_trained: string;
  training_samples: number;
}

// WebSocket Message Types
export type WebSocketMessageType =
  | 'CASE_UPDATED'
  | 'NEW_CASE'
  | 'CHAT_MESSAGE'
  | 'NOTIFICATION'
  | 'AGENT_STREAM'
  | 'HEARTBEAT';

export interface WebSocketMessage<T = any> {
  type: WebSocketMessageType;
  payload: T;
  timestamp: string;
  request_id?: string;
}

export interface CaseUpdateMessage {
  case_id: string;
  updates: Partial<Case>;
  updated_by: string;
}

export interface NotificationMessage {
  id: string;
  type: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';
  title: string;
  message: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  action_url?: string;
  read: boolean;
  timestamp: string;
}

// API Response Types
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Filter and Query Types
export interface CaseFilters {
  status?: CaseStatus[];
  risk_level?: RiskLevel[];
  assigned_analyst?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface CaseQuery {
  filters?: CaseFilters;
  sort_by?: 'created_at' | 'risk_score' | 'updated_at';
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

// Form Types
export interface CaseActionForm {
  action: 'APPROVE' | 'BLOCK' | 'ESCALATE' | 'REQUEST_INFO';
  reason: string;
  notes?: string;
}

export interface VerificationAnswer {
  question_id: string;
  answer: string | boolean | number;
}

// Utility Types
export type AsyncStatus = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data: T | null;
  status: AsyncStatus;
  error: Error | null;
}

// Export utility type helpers
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type Required<T, K extends keyof T> = T & { [P in K]-?: T[P] };

