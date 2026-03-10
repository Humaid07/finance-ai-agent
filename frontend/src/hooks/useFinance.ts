import { useQuery, useMutation } from '@tanstack/react-query'
import { financeApi } from '../api/finance'

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: financeApi.getDashboard,
  })
}

export function useTrialBalance(params?: { date_from?: string; date_to?: string }) {
  return useQuery({
    queryKey: ['trial-balance', params],
    queryFn: () => financeApi.getTrialBalance(params),
  })
}

export function usePnL(params?: { date_from?: string; date_to?: string }) {
  return useQuery({
    queryKey: ['pnl', params],
    queryFn: () => financeApi.getPnL(params),
  })
}

export function useHierarchyTree() {
  return useQuery({
    queryKey: ['hierarchy-tree'],
    queryFn: financeApi.getHierarchyTree,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useJournalLines(params?: {
  page?: string
  page_size?: string
  date_from?: string
  date_to?: string
}) {
  return useQuery({
    queryKey: ['journal-lines', params],
    queryFn: () => financeApi.getJournalLines(params),
  })
}

export function useJournalEntries(params?: { page?: string }) {
  return useQuery({
    queryKey: ['journal-entries', params],
    queryFn: () => financeApi.getJournalEntries(params),
  })
}

export function useChat() {
  return useMutation({
    mutationFn: ({ question, history }: { question: string; history: { role: string; content: string }[] }) =>
      financeApi.chat(question, history),
  })
}
