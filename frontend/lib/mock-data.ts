/**
 * Mock data for local development when AWS is not set up
 */

export const mockDashboardStats = {
  active_cases: 12,
  high_risk_cases: 3,
  resolved_today: 5,
  total_cases: 267,
  avg_risk_score: 64.5,
  fraud_detection_rate: 96.8,
  false_positive_rate: 2.3
}

export const mockCases = [
  {
    case_id: 'AEGIS-CASE-00000001',
    customer_id: 'AEGIS-CUST-000001',
    transaction_id: 'AEGIS-TXN-00000001',
    case_type: 'Investment Scam',
    priority: 'High',
    status: 'In Progress',
    created_date: new Date().toISOString().split('T')[0],
    assigned_analyst_name: 'Sarah Johnson',
    risk_score: 85
  },
  {
    case_id: 'AEGIS-CASE-00000002',
    customer_id: 'AEGIS-CUST-000002',
    transaction_id: 'AEGIS-TXN-00000002',
    case_type: 'Romance Scam',
    priority: 'Critical',
    status: 'Open',
    created_date: new Date().toISOString().split('T')[0],
    assigned_analyst_name: 'Michael Chen',
    risk_score: 92
  },
  {
    case_id: 'AEGIS-CASE-00000003',
    customer_id: 'AEGIS-CUST-000003',
    transaction_id: 'AEGIS-TXN-00000003',
    case_type: 'Invoice Fraud',
    priority: 'Medium',
    status: 'Pending Review',
    created_date: new Date().toISOString().split('T')[0],
    assigned_analyst_name: 'Emily Williams',
    risk_score: 68
  },
  {
    case_id: 'AEGIS-CASE-00000004',
    customer_id: 'AEGIS-CUST-000004',
    transaction_id: 'AEGIS-TXN-00000004',
    case_type: 'Crypto Scam',
    priority: 'High',
    status: 'In Progress',
    created_date: new Date().toISOString().split('T')[0],
    assigned_analyst_name: 'David Brown',
    risk_score: 88
  },
  {
    case_id: 'AEGIS-CASE-00000005',
    customer_id: 'AEGIS-CUST-000005',
    transaction_id: 'AEGIS-TXN-00000005',
    case_type: 'APP Scam',
    priority: 'Low',
    status: 'Resolved - False Positive',
    created_date: new Date().toISOString().split('T')[0],
    assigned_analyst_name: 'Jessica Lee',
    risk_score: 45
  }
]

export const useMockData = () => {
  // Check if we should use mock data
  const isLocalDev = typeof window !== 'undefined' && 
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  
  // Check if AWS is configured
  const hasAWSConfig = process.env.NEXT_PUBLIC_API_URL !== undefined
  
  return isLocalDev && !hasAWSConfig
}





