import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { useChat } from '../hooks/useFinance'
import type { ChatMessage } from '../types/finance'
import EvidencePanel from '../components/EvidencePanel'
import PageHeader from '../components/PageHeader'
import clsx from 'clsx'

const SUGGESTED_QUESTIONS = [
  'What is the balance of cash?',
  'Show me the P&L summary',
  'What are the top 5 expense accounts?',
  'Why did travel expenses change?',
  'Show the trial balance',
]

export default function AIChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        "Hello! I'm your Finance AI Assistant. I can answer questions about your GL accounts, trial balance, P&L, expenses, and journal entries. Ask me anything about your financial data.",
      evidence: [],
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const endRef = useRef<HTMLDivElement>(null)
  const chatMutation = useChat()

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (question: string) => {
    if (!question.trim()) return

    const userMsg: ChatMessage = {
      role: 'user',
      content: question,
      evidence: [],
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')

    const history = messages.map((m) => ({ role: m.role, content: m.content }))

    try {
      const result = await chatMutation.mutateAsync({ question, history })
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: result.answer,
        evidence: result.evidence,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          evidence: [],
          timestamp: new Date(),
        },
      ])
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      <PageHeader
        title="AI Finance Assistant"
        subtitle="Ask questions about your financial data"
      />

      {/* Suggested questions */}
      <div className="flex gap-2 flex-wrap mb-4">
        {SUGGESTED_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => sendMessage(q)}
            className="text-xs px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors border border-blue-200"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto card p-4 space-y-4 mb-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={clsx('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                <Bot size={16} className="text-blue-600" />
              </div>
            )}
            <div className={clsx('max-w-2xl', msg.role === 'user' ? 'order-first' : '')}>
              <div
                className={clsx(
                  'rounded-2xl px-4 py-3 text-sm leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white ml-auto'
                    : 'bg-gray-100 text-gray-800'
                )}
              >
                {msg.content}
              </div>
              {msg.role === 'assistant' && msg.evidence && msg.evidence.length > 0 && (
                <EvidencePanel evidence={msg.evidence} />
              )}
              <div className="text-xs text-gray-400 mt-1 px-1">
                {msg.timestamp.toLocaleTimeString()}
              </div>
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                <User size={16} className="text-gray-600" />
              </div>
            )}
          </div>
        ))}
        {chatMutation.isPending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center shrink-0">
              <Loader2 size={16} className="text-blue-600 animate-spin" />
            </div>
            <div className="bg-gray-100 rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
          placeholder="Ask a finance question... (e.g. What is the cash balance?)"
          className="flex-1 input text-sm"
          disabled={chatMutation.isPending}
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || chatMutation.isPending}
          className="btn-primary flex items-center gap-2 disabled:opacity-50"
        >
          <Send size={16} />
          Send
        </button>
      </div>
    </div>
  )
}
