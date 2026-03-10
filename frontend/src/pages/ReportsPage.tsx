import { useState } from 'react'
import { useTrialBalance, usePnL } from '../hooks/useFinance'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import clsx from 'clsx'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

const accountTypeColors: Record<string, string> = {
  ASSET: 'text-blue-700',
  LIABILITY: 'text-red-700',
  EQUITY: 'text-purple-700',
  REVENUE: 'text-emerald-700',
  EXPENSE: 'text-orange-700',
}

export default function ReportsPage() {
  const [tab, setTab] = useState<'trial-balance' | 'pnl'>('trial-balance')
  const { data: tb, isLoading: tbLoading, error: tbError } = useTrialBalance()
  const { data: pnl, isLoading: pnlLoading, error: pnlError } = usePnL()

  return (
    <div>
      <PageHeader title="Financial Reports" subtitle="Trial balance and profit & loss analysis" />

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-5">
        {(['trial-balance', 'pnl'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={clsx(
              'px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              tab === t
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            {t === 'trial-balance' ? 'Trial Balance' : 'Profit & Loss'}
          </button>
        ))}
      </div>

      {tab === 'trial-balance' && (
        <div className="card">
          {tbLoading && <LoadingSpinner />}
          {tbError && <ErrorMessage message={tbError.message} />}
          {tb && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Code</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Account</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Type</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Debit</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Credit</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-500">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {tb.map((row) => (
                    <tr key={row.account_code} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-500">{row.account_code}</td>
                      <td className="px-4 py-2.5 text-gray-800">{row.account_name}</td>
                      <td className={clsx('px-4 py-2.5 text-xs font-medium', accountTypeColors[row.account_type])}>
                        {row.account_type}
                      </td>
                      <td className="px-4 py-2.5 text-right text-gray-600">{fmt(row.debit)}</td>
                      <td className="px-4 py-2.5 text-right text-gray-600">{fmt(row.credit)}</td>
                      <td className={clsx(
                        'px-4 py-2.5 text-right font-semibold',
                        row.balance >= 0 ? 'text-gray-900' : 'text-red-600'
                      )}>
                        {fmt(row.balance)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'pnl' && (
        <div className="space-y-4">
          {pnlLoading && <LoadingSpinner />}
          {pnlError && <ErrorMessage message={pnlError.message} />}
          {pnl && (
            <>
              {/* Summary cards */}
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: 'Revenue', value: pnl.revenue, color: 'text-emerald-600' },
                  { label: 'Expenses', value: pnl.expenses, color: 'text-red-600' },
                  { label: 'Net Income', value: pnl.net_income, color: pnl.net_income >= 0 ? 'text-emerald-600' : 'text-red-600' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="card p-4 text-center">
                    <div className="text-sm text-gray-500">{label}</div>
                    <div className={clsx('text-2xl font-bold mt-1', color)}>{fmt(value)}</div>
                  </div>
                ))}
              </div>

              {/* Expense breakdown chart */}
              <div className="card p-5">
                <h3 className="text-sm font-semibold text-gray-700 mb-4">Expense Breakdown</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={pnl.expense_breakdown} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="account" width={150} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v: number) => fmt(v)} />
                    <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                      {pnl.expense_breakdown.map((_, i) => (
                        <Cell key={i} fill={i % 2 === 0 ? '#ef4444' : '#f97316'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
