import { useRef, useState } from 'react'
import './ChatWidget.css'

const API = import.meta.env.DEV ? 'http://127.0.0.1:8000' : ''

const PRESETS = [
  '他做 RAG 踩过什么坑？',
  '无来源不答是怎么实现的？',
  '他主要会哪些技术栈？',
  'OpsPilot 和普通 QA 项目有何不同？',
]

const SOURCE_LABELS = {
  'ops-pilot': 'OpsPilot',
  agenthub: 'AgentHub',
  'legal-assistant': '劳动法律助手',
  'finetune-deploy': '大模型微调与部署',
  resume: '简历',
}

function SourceList({ hits }) {
  if (!hits?.length) return null
  return (
    <div className="sources">
      <div className="sources-title">来源（点击可查）</div>
      <ul>
        {hits.map((h, i) => (
          <li key={i}>
            <span className="src-badge">[{i + 1}] {SOURCE_LABELS[h.source] || h.source}</span>
            <span className="src-text">{h.text.slice(0, 60)}…</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const listRef = useRef(null)

  function scrollToBottom() {
    setTimeout(() => {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
    }, 50)
  }

  async function ask(q) {
    const question = (q ?? input).trim()
    if (!question || busy) return
    setMsgs((m) => [...m, { role: 'user', content: question }])
    setInput('')
    setBusy(true)
    try {
      const r = await fetch(`${API}/api/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      const data = await r.json()
      setMsgs((m) => [...m, { role: 'assistant', content: data.answer, hits: data.hits }])
    } catch {
      // 静态托管（GitHub Pages）下没有后端 /api/chat，给出可理解的提示
      setMsgs((m) => [
        ...m,
        {
          role: 'assistant',
          content: API
            ? '服务出错了，请稍后再试。'
            : '当前是静态展示版，AI 问答需要连接后端演示服务；完整版请访问仓库 README 中的在线演示链接。',
        },
      ])
    }
    setBusy(false)
    scrollToBottom()
  }

  return (
    <>
      {!open && (
        <button className="chat-fab" onClick={() => setOpen(true)} aria-label="向我提问">
          ?
        </button>
      )}

      {open && (
        <div className="chat-panel">
          <div className="chat-head">
            <span className="chat-title">向我提问</span>
            <button className="chat-close" onClick={() => setOpen(false)}>×</button>
          </div>

          <div className="presets">
            {PRESETS.map((p) => (
              <button key={p} className="preset" disabled={busy} onClick={() => ask(p)}>{p}</button>
            ))}
          </div>

          <div className="chat-list" ref={listRef}>
            {msgs.length === 0 && (
              <div className="chat-empty">你可以问我关于项目、技术栈的任何问题，我只会基于真实资料作答。</div>
            )}
            {msgs.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                <div className="bubble">{m.content}</div>
                {m.role === 'assistant' && <SourceList hits={m.hits} />}
              </div>
            ))}
            {busy && <div className="msg assistant"><div className="bubble typing">…</div></div>}
          </div>

          <form
            className="chat-input-row"
            onSubmit={(e) => { e.preventDefault(); ask() }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入你的问题…"
              disabled={busy}
            />
            <button type="submit" disabled={busy || !input.trim()}>发送</button>
          </form>
        </div>
      )}
    </>
  )
}