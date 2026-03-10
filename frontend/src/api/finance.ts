import { api } from './client'
import type {
  DashboardData,
  TrialBalanceRow,
  PnLResult,
  PaginatedResult,
  JournalLine,
  JournalEntry,
  HierarchyNode,
  ChatResponse,
} from '../types/finance'

export const financeApi = {
  getDashboard: () => api.get<DashboardData>('reports/dashboard'),

  getTrialBalance: (params?: { date_from?: string; date_to?: string }) =>
    api.get<TrialBalanceRow[]>('reports/trial-balance', params as Record<string, string>),

  getPnL: (params?: { date_from?: string; date_to?: string }) =>
    api.get<PnLResult>('reports/pnl', params as Record<string, string>),

  getHierarchyTree: () => api.get<HierarchyNode[]>('hierarchy/tree'),

  getJournalLines: (params?: {
    page?: string
    page_size?: string
    date_from?: string
    date_to?: string
    account_id?: string
  }) =>
    api.get<PaginatedResult<JournalLine>>(
      'transactions/journal-lines',
      params as Record<string, string>
    ),

  getJournalEntries: (params?: { page?: string; page_size?: string }) =>
    api.get<PaginatedResult<JournalEntry>>(
      'transactions/journal-entries',
      params as Record<string, string>
    ),

  chat: (question: string, history: { role: string; content: string }[]) =>
    api.post<ChatResponse>('ai/chat', { question, history }),
}
