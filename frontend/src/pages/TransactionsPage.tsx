import { useState } from 'react'
import { useJournalLines, useJournalEntries } from '../hooks/useFinance'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import clsx from 'clsx'
import { ChevronLeft, ChevronRight } from 'lucide-react'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

export default function TransactionsPage() {
  const [tab, setTab] = useState<'lines' | 'entries'>('lines')
  const [page, setPage] = useState(1)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const linesQuery = useJournalLines({
    page: String(page),
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  })

  const entriesQuery = useJournalEntries({ page: String(page) })

  const handleFilter = () => {
    setPage(1)
  }

  return (
    <div>
      <PageHeader title="Transactions" subtitle="Journal entries and posting lines" />

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-5">
        {(['lines', 'entries'] as const).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setPage(1) }}
            className={clsx(
              'px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              tab === t
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            {t === 'lines' ? 'Journal Lines' : 'Journal Entries'}
          </button>
        ))}
      </div>

      {/* Filters */}
      {tab === 'lines' && (
        <div className="flex gap-3 mb-4 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Date From</label>
            <input type="date" className="input text-sm" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Date To</label>
            <input type="date" className="input text-sm" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
          <button onClick={handleFilter} className="btn-primary text-sm">Filter</button>
          <button onClick={() => { setDateFrom(''); setDateTo(''); setPage(1) }} className="btn-secondary text-sm">Clear</button>
        </div>
      )}

      {/* Journal Lines Table */}
      {tab === 'lines' && (
        <div className="card">
          {linesQuery.isLoading && <LoadingSpinner />}
          {linesQuery.error && <ErrorMessage message={linesQuery.error.message} />}
          {linesQuery.data && (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Date</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Account</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Description</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-500">Debit</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-500">Credit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {linesQuery.data.items.map((line) => (
                      <tr key={line.id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="px-4 py-2.5 text-gray-500 text-xs whitespace-nowrap">{line.posting_date}</td>
                        <td className="px-4 py-2.5">
                          <div className="text-gray-800 font-medium">{line.account_name}</div>
                          <div className="text-xs text-gray-400 font-mono">{line.account_code}</div>
                        </td>
                        <td className="px-4 py-2.5 text-gray-600 text-xs max-w-xs truncate">{line.description || '—'}</td>
                        <td className="px-4 py-2.5 text-right text-gray-800">{line.debit > 0 ? fmt(line.debit) : ''}</td>
                        <td className="px-4 py-2.5 text-right text-gray-800">{line.credit > 0 ? fmt(line.credit) : ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={page}
                pages={linesQuery.data.pages}
                total={linesQuery.data.total}
                onPage={setPage}
              />
            </>
          )}
        </div>
      )}

      {/* Journal Entries Table */}
      {tab === 'entries' && (
        <div className="card">
          {entriesQuery.isLoading && <LoadingSpinner />}
          {entriesQuery.error && <ErrorMessage message={entriesQuery.error.message} />}
          {entriesQuery.data && (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Entry #</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Date</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Description</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-500">Period</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-500">Lines</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entriesQuery.data.items.map((entry) => (
                      <tr key={entry.id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="px-4 py-2.5 font-mono text-xs text-blue-600">{entry.entry_number}</td>
                        <td className="px-4 py-2.5 text-gray-500 text-xs">{entry.posting_date}</td>
                        <td className="px-4 py-2.5 text-gray-800">{entry.description}</td>
                        <td className="px-4 py-2.5 text-gray-500 text-xs">{entry.period}</td>
                        <td className="px-4 py-2.5 text-right text-gray-600">{entry.line_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={page}
                pages={entriesQuery.data.pages}
                total={entriesQuery.data.total}
                onPage={setPage}
              />
            </>
          )}
        </div>
      )}
    </div>
  )
}

function Pagination({ page, pages, total, onPage }: {
  page: number; pages: number; total: number; onPage: (p: number) => void
}) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
      <span className="text-xs text-gray-500">{total.toLocaleString()} records</span>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPage(page - 1)}
          disabled={page <= 1}
          className="p-1 rounded hover:bg-gray-100 disabled:opacity-40"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-xs text-gray-600">Page {page} of {pages}</span>
        <button
          onClick={() => onPage(page + 1)}
          disabled={page >= pages}
          className="p-1 rounded hover:bg-gray-100 disabled:opacity-40"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}
