import { DollarSign, TrendingUp, TrendingDown, BookOpen } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useDashboard } from '../hooks/useFinance'
import KpiCard from '../components/KpiCard'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

export default function DashboardPage() {
  const { data, isLoading, error } = useDashboard()

  if (isLoading) return <LoadingSpinner message="Loading dashboard..." />
  if (error) return <ErrorMessage message={error.message} />
  if (!data) return null

  const netPositive = data.net_income >= 0

  return (
    <div>
      <PageHeader
        title="Financial Dashboard"
        subtitle="Key performance indicators and financial summary"
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <KpiCard
          title="Total Revenue"
          value={fmt(data.total_revenue)}
          icon={TrendingUp}
          color="green"
          trend="up"
          trendValue="YTD"
        />
        <KpiCard
          title="Total Expenses"
          value={fmt(data.total_expenses)}
          icon={TrendingDown}
          color="red"
          trend="neutral"
          trendValue="YTD"
        />
        <KpiCard
          title="Net Income"
          value={fmt(data.net_income)}
          icon={DollarSign}
          color={netPositive ? 'green' : 'red'}
          trend={netPositive ? 'up' : 'down'}
          trendValue={netPositive ? 'Profitable' : 'Loss'}
        />
        <KpiCard
          title="Journal Entries"
          value={data.journal_entry_count.toLocaleString()}
          subtitle={`${data.journal_line_count.toLocaleString()} lines`}
          icon={BookOpen}
          color="blue"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-6">
        {/* Revenue by Period */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Revenue by Period</h3>
          {data.revenue_by_period.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.revenue_by_period}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v: number) => fmt(v)} />
                <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">No revenue data</div>
          )}
        </div>

        {/* Top Expense Accounts */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Top Expense Accounts</h3>
          {data.top_expense_accounts.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={data.top_expense_accounts}
                  dataKey="balance"
                  nameKey="account_name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, percent }: { name: string; percent: number }) => `${name?.split(' ')[0]} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {data.top_expense_accounts.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => fmt(v)} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">No expense data</div>
          )}
        </div>
      </div>

      {/* Top Expenses Table */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Top Expense Accounts</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-2 font-medium text-gray-500">Account</th>
                <th className="text-left py-2 font-medium text-gray-500">Code</th>
                <th className="text-right py-2 font-medium text-gray-500">Balance</th>
              </tr>
            </thead>
            <tbody>
              {data.top_expense_accounts.map((acct) => (
                <tr key={acct.account_code} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2.5 text-gray-800">{acct.account_name}</td>
                  <td className="py-2.5 text-gray-500 font-mono text-xs">{acct.account_code}</td>
                  <td className="py-2.5 text-right font-medium text-gray-900">{fmt(acct.balance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
