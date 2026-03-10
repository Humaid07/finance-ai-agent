import type { EvidenceItem } from '../types/finance'
import { Database } from 'lucide-react'

interface EvidencePanelProps {
  evidence: EvidenceItem[]
}

export default function EvidencePanel({ evidence }: EvidencePanelProps) {
  if (evidence.length === 0) return null

  return (
    <div className="mt-3 space-y-2">
      {evidence.map((e, i) => (
        <div key={i} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <Database size={13} className="text-blue-500" />
            <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">
              {e.tool.replace(/_/g, ' ')}
            </span>
          </div>
          <pre className="text-xs text-gray-600 overflow-auto max-h-32 whitespace-pre-wrap">
            {JSON.stringify(e.result, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  )
}
