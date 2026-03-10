export interface TrialBalanceRow {
  account_code: string
  account_name: string
  account_type: string
  debit: number
  credit: number
  balance: number
}

export interface PnLResult {
  revenue: number
  expenses: number
  net_income: number
  revenue_breakdown: { account: string; amount: number }[]
  expense_breakdown: { account: string; amount: number }[]
  period: string
}

export interface DashboardData {
  total_revenue: number
  total_expenses: number
  net_income: number
  journal_entry_count: number
  journal_line_count: number
  top_expense_accounts: { account_code: string; account_name: string; balance: number }[]
  revenue_by_period: { period: string; revenue: number }[]
}

export interface JournalLine {
  id: string
  journal_entry_id: string
  account_id: string
  account_name: string | null
  account_code: string | null
  debit: number
  credit: number
  posting_date: string
  description: string | null
  document_reference: string | null
  currency_code: string
}

export interface JournalEntry {
  id: string
  entry_number: string
  description: string | null
  posting_date: string
  period: string
  status: string
  document_reference: string | null
  line_count: number
}

export interface PaginatedResult<T> {
  total: number
  page: number
  page_size: number
  pages: number
  items: T[]
}

export interface HierarchyNode {
  id: string
  code: string
  name: string
  type: 'company' | 'entity' | 'ledger' | 'account_group' | 'gl_account'
  account_type?: string
  children?: HierarchyNode[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  evidence?: EvidenceItem[]
  timestamp: Date
}

export interface EvidenceItem {
  tool: string
  arguments: Record<string, unknown>
  result: unknown
}

export interface ChatResponse {
  answer: string
  evidence: EvidenceItem[]
}
