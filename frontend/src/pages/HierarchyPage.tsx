import { useHierarchyTree } from '../hooks/useFinance'
import HierarchyTree from '../components/HierarchyTree'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

export default function HierarchyPage() {
  const { data, isLoading, error } = useHierarchyTree()

  return (
    <div>
      <PageHeader
        title="GL Hierarchy Explorer"
        subtitle="Browse the full General Ledger account hierarchy"
      />
      <div className="card p-5">
        {isLoading && <LoadingSpinner message="Loading hierarchy..." />}
        {error && <ErrorMessage message={error.message} />}
        {data && data.length > 0 && <HierarchyTree nodes={data} />}
        {data && data.length === 0 && (
          <div className="text-center py-12 text-gray-400 text-sm">
            No hierarchy data found. Run the seed script to populate sample data.
          </div>
        )}
      </div>
    </div>
  )
}
