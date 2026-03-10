import { useState } from 'react'
import { ChevronRight, ChevronDown, Building2, Globe, BookOpen, FolderOpen, Hash } from 'lucide-react'
import type { HierarchyNode } from '../types/finance'
import clsx from 'clsx'

const typeIcons: Record<string, React.ElementType> = {
  company: Building2,
  entity: Globe,
  ledger: BookOpen,
  account_group: FolderOpen,
  gl_account: Hash,
}

const typeBadgeColors: Record<string, string> = {
  ASSET: 'bg-blue-100 text-blue-700',
  LIABILITY: 'bg-red-100 text-red-700',
  EQUITY: 'bg-purple-100 text-purple-700',
  REVENUE: 'bg-emerald-100 text-emerald-700',
  EXPENSE: 'bg-orange-100 text-orange-700',
}

interface TreeNodeProps {
  node: HierarchyNode
  depth?: number
}

function TreeNode({ node, depth = 0 }: TreeNodeProps) {
  const [expanded, setExpanded] = useState(depth < 2)
  const hasChildren = node.children && node.children.length > 0
  const Icon = typeIcons[node.type] || Hash

  return (
    <div>
      <div
        className={clsx(
          'flex items-center gap-2 py-1.5 px-2 rounded-lg cursor-pointer hover:bg-gray-50 group',
          depth === 0 && 'font-semibold text-gray-800'
        )}
        style={{ paddingLeft: `${8 + depth * 18}px` }}
        onClick={() => hasChildren && setExpanded((e) => !e)}
      >
        <span className="w-4 shrink-0 text-gray-400">
          {hasChildren ? (
            expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />
          ) : null}
        </span>
        <Icon size={15} className="text-gray-400 shrink-0" />
        <span className="text-sm text-gray-700">{node.name}</span>
        <span className="text-xs text-gray-400">({node.code})</span>
        {node.account_type && (
          <span
            className={clsx(
              'ml-auto text-xs px-1.5 py-0.5 rounded font-medium',
              typeBadgeColors[node.account_type] || 'bg-gray-100 text-gray-600'
            )}
          >
            {node.account_type}
          </span>
        )}
      </div>
      {expanded && hasChildren && (
        <div>
          {node.children!.map((child) => (
            <TreeNode key={child.id} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

interface HierarchyTreeProps {
  nodes: HierarchyNode[]
}

export default function HierarchyTree({ nodes }: HierarchyTreeProps) {
  return (
    <div className="space-y-1">
      {nodes.map((node) => (
        <TreeNode key={node.id} node={node} />
      ))}
    </div>
  )
}
