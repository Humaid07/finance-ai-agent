import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  GitBranch,
  FileBarChart,
  BookOpen,
  MessageSquareText,
  TrendingUp,
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/hierarchy', icon: GitBranch, label: 'GL Hierarchy' },
  { to: '/reports', icon: FileBarChart, label: 'Reports' },
  { to: '/transactions', icon: BookOpen, label: 'Transactions' },
  { to: '/ai-chat', icon: MessageSquareText, label: 'AI Assistant' },
]

export default function Sidebar() {
  return (
    <aside className="w-60 bg-[#1e2a3b] flex flex-col shrink-0 h-full">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-[#2d3f56]">
        <div className="flex items-center gap-2.5">
          <TrendingUp className="text-blue-400" size={22} />
          <div>
            <div className="text-white font-semibold text-sm leading-tight">Finance AI</div>
            <div className="text-[#94a3b8] text-xs">Analytics Platform</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-[#94a3b8] hover:bg-[#2d3f56] hover:text-white'
              )
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-[#2d3f56]">
        <div className="text-[#475569] text-xs">Finance AI Agent v1.0</div>
      </div>
    </aside>
  )
}
