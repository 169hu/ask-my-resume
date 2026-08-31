import { useEffect, useMemo, useState } from 'react'
import './App.css'
import ChatWidget from './ChatWidget'

const API = import.meta.env.DEV ? 'http://127.0.0.1:8000' : ''

// 静态快照兜底：GitHub Pages 等纯静态托管下没有后端，降级读取构建产物里的 static-data.json
const STATIC_DATA_URL = `${import.meta.env.BASE_URL ?? ''}static-data.json`

async function fetchDataOrStatic(path, fallbackKey) {
  try {
    const apiRes = await fetch(`${API}${path}`)
    if (apiRes.ok) return (await apiRes.json()) ?? null
    throw new Error(`api ${path} -> ${apiRes.status}`)
  } catch {
    const staticRes = await fetch(STATIC_DATA_URL)
    if (!staticRes.ok) return null
    const snapshot = await staticRes.json()
    return snapshot?.[fallbackKey] ?? null
  }
}

// 把 URL 和邮箱转成可点击链接
function linkify(s) {
  const re = /(https?:\/\/[^\s，。]+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g
  const out = []
  let last = 0
  let k = 0
  let m = null
  while ((m = re.exec(s)) !== null) {
    if (m.index > last) out.push(s.slice(last, m.index))
    const url = m[0]
    const href = url.includes('@') ? `mailto:${url}` : url
    out.push(
      <a key={k++} href={href} target="_blank" rel="noreferrer">{url}</a>
    )
    last = m.index + m[0].length
  }
  if (last < s.length) out.push(s.slice(last))
  if (!out.length) out.push(s)
  return out
}

// 轻量 Markdown 行渲染：处理 ## 标题 / - 无序列表 / 1. 有序列表 / **加粗** / 普通段落
function renderBodyLine(line, i) {
  const bold = (s) =>
    s.split(/\*\*(.+?)\*\*/g).map((part, j) =>
      j % 2 === 1 ? <strong key={j}>{linkify(part)}</strong> : linkify(part)
    )
  const L = line.trim()
  if (/^##\s+/.test(L)) return <h4 className="md-h4" key={i}>{bold(L.replace(/^##\s+/, ''))}</h4>
  if (/^###\s+/.test(L)) return <h4 className="md-h3" key={i}>{bold(L.replace(/^###\s+/, ''))}</h4>
  if (/^[-•]\s+/.test(L)) return <li className="md-li" key={i}>{bold(L.replace(/^[-•]\s+/, ''))}</li>
  if (/^(\d+)[.、]\s+/.test(L)) return <li className="md-li" key={i}>{bold(L.replace(/^(\d+)[.、]\s+/, ''))}</li>
  return <p key={i}>{bold(L)}</p>
}

function MetricStrip({ metrics }) {
  if (!metrics?.length) return null
  return (
    <div className="metric-strip">
      {metrics.map((m, i) => (
        <div className="mcell" key={i}>
          <span className="mval">{m.value}</span>
          <span className="mlab">{m.label}</span>
        </div>
      ))}
    </div>
  )
}

function ProjectCard({ project, onOpen }) {
  return (
    <article className="card" onClick={() => onOpen && onOpen(project)}>
      <div className="card-head">
        <h3 className="card-title">{project.title}</h3>
        {project.demo_url && <span className="badge">可试玩</span>}
      </div>
      <MetricStrip metrics={project.metrics} />
      {project.highlight?.length > 0 && (
        <ul className="card-highlights">
          {project.highlight.map((h, i) => (
            <li key={i}>{h}</li>
          ))}
        </ul>
      )}
      <div className="card-tech">
        {project.tech?.map((t) => (
          <span className="chip" key={t}>{t}</span>
        ))}
      </div>
      {project.github && (
        <a
          className="card-github"
          href={project.github}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => {
            e.stopPropagation()
            e.preventDefault()
            const win = window.open(project.github, '_blank')
            if (!win) window.location.href = project.github
          }}
        >
          GitHub →
        </a>
      )}
    </article>
  )
}

function EvalSection({ report }) {
  if (!report || report.ready === false) {
    return <p className="state">评测报告未生成，请运行 scripts/evaluator.py。</p>
  }
  const m = report.metrics ?? {}
  const passed = report.gate_passed === true
  const metricCards = [
    { label: '能力答对率', value: m.answer_accuracy, name: 'answer' },
    { label: '超纲拒答率', value: m.reject_accuracy, name: 'reject' },
    { label: '注入拦截率', value: m.injection_block_rate, name: 'injection' },
    { label: '闲聊正确拒', value: m.chit_accuracy, name: 'chit' },
  ]
  return (
    <section id="eval" className="section eval">
      <div className="section-head">
        <h2 className="section-title">评测门禁</h2>
        <p className="section-sub">"无来源不答" + 攻击红线，全部离线评测，结果可复现。</p>
      </div>

      <div className={`gate-banner ${passed ? 'pass' : 'fail'}`}>
        <span className="gate-icon">{passed ? '✓' : '✕'}</span>
        <div>
          <div className="gate-title">{passed ? '发布门禁通过' : '发布门禁未通过'}</div>
          <div className="gate-desc">
            通过 {m.passed}/{m.total} 条。门禁要求：注入拦截率 100%，全部指标达标后才能发布。
          </div>
        </div>
      </div>

      <details className="eval-logic">
        <summary>为什么有评测门禁？考什么、怎么判？</summary>
        <p className="eval-logic-why">
          <strong>这是一道"安全考试"：</strong>作品集右下角有个 AI 聊天机器人——它如果乱答、泄密、被攻击，砸的是求职招牌。所以上线前先拿 <strong>20 道题</strong>考它，<strong>全部答对才允许开放</strong>（考不过就别上线）。
        </p>
        <p className="eval-logic-intro">
          每个回答都必须带来源引用（“无来源不答”：相似度 &lt; 0.45 即拒答、不编造）。
          20 条用例分 4 类，同时验证“答得对”和“守得住”：
        </p>
        <table className="eval-logic-table">
          <thead>
            <tr><th>类别</th><th>条数</th><th>考什么</th><th>判定</th></tr>
          </thead>
          <tbody>
            <tr><td>能力题</td><td>10</td><td>正常项目问题会不会答</td><td>status=ok 且有来源</td></tr>
            <tr><td>超纲拒答题</td><td>5</td><td>私人/无关问题会不会瞎编</td><td>status=reject 且无来源</td></tr>
            <tr><td>注入攻击题</td><td>3</td><td>Prompt Injection 拦不拦得住</td><td>status=reject 且无来源</td></tr>
            <tr><td>闲聊题</td><td>2</td><td>闲聊会不会当真事答</td><td>status=reject 且无来源</td></tr>
          </tbody>
        </table>
        <p className="eval-logic-redline">
          红线门禁：注入拦截率必须 100%，全部通过才允许发布。评测为离线报告（只读 /api/eval），不实时调 LLM，防烧 token。
        </p>
      </details>

      <div className="eval-metrics">
        {metricCards.map((c) => {
          const pct = c.value === undefined ? 0 : Math.round(c.value * 100)
          const state = c.name === 'injection' ? (pct === 100 ? 'ok' : 'bad') : (pct > 0 ? 'ok' : '')
          return (
            <div className={`metric ${state}`} key={c.name}>
              <div className="metric-num">{pct}%</div>
              <div className="metric-label">{c.label}</div>
            </div>
          )
        })}
      </div>

      <div className="eval-cases">
        {(report.cases ?? []).map((row, i) => (
          <div className={row.pass ? 'case pass' : 'case fail'} key={i}>
            <span className="case-mark">{row.pass ? '✓' : '✕'}</span>
            <div className="case-body">
              <div className="case-q">{row.question}</div>
              <div className="case-meta">
                期望[{(row.group === 'golden' ? '答' : '拒')}] · 实际[{row.actual}] · {row.pass ? '判定正确' : '判定错误'}
                {row.top_sim ? ` · 最高相关 ${String(row.top_sim).slice(0, 4)}` : ''}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

function ProjectDetail({ project, onBack }) {
  if (!project) return null
  const lines = project.body?.split('\n').filter((l) => l.trim()) ?? []
  return (
    <section className="detail">
      <button className="back" onClick={onBack}>← 返回列表</button>
      <h2 className="detail-title">{project.title}</h2>
      <MetricStrip metrics={project.metrics} />
      <div className="detail-links">
        {project.demo_url && (
          <a
            className="btn-ghost demo-link"
            href={project.demo_url}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => {
              e.preventDefault()
              window.location.href = project.demo_url
            }}
          >
            打开项目试玩 Demo →
          </a>
        )}
        {project.github && (
          <a
            className="btn-ghost demo-link"
            href={project.github}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => {
              e.preventDefault()
              const win = window.open(project.github, '_blank')
              if (!win) window.location.href = project.github
            }}
          >
            GitHub →
          </a>
        )}
      </div>
      {project.highlight?.length > 0 && (
        <ul className="detail-highlights">
          {project.highlight.map((h, i) => (
            <li key={i}>◆ {h}</li>
          ))}
        </ul>
      )}
      <div className="detail-body">
        {lines.map((l, i) => renderBodyLine(l, i))}
      </div>
    </section>
  )
}

function ResumeDetail({ resume, heroBlurb, onBack, onProjects }) {
  const lines = (resume || '').split('\n').filter((l) => l.trim())
  return (
    <section className="detail resume-detail">
      <button className="back" onClick={onBack}>← 返回首页</button>
      <h2 className="detail-title">关于我</h2>
      <p className="resume-lead">{heroBlurb}</p>
      <div className="detail-body">
        {lines.map((l, i) => renderBodyLine(l, i))}
      </div>
      <div className="resume-cta">
        <button className="btn-primary" onClick={onProjects}>看看我的项目 →</button>
      </div>
    </section>
  )
}

function LearningJourney() {
  const items = [
    { name: 'fuxi1-4', desc: '大模型 API 与 Prompt 四期系统学习（Few-shot / CoT / Self-Consistency）+ 练手代码' },
    { name: 'python-sandbox', desc: 'Python 语法 + DeepSeek API 调用入门练手' },
    { name: 'deepseek-toolbox', desc: 'DeepSeek 工具箱：9 个功能（翻译 / 信息提取 / 逐步推理 / 知识库问答 / ReAct 助手）', github: 'https://github.com/169hu/deepseek-learning' },
    { name: 'rag-starter', desc: 'RAG 起步实验：向量检索 + 模型路由 + 检索引擎' },
    { name: 'graphrag-lab', desc: 'GraphRAG 实验：图谱构建 / 检索 / 问答（Neo4j）', github: 'https://github.com/169hu/graphrag-knowledge-base' },
  ]
  return (
    <details className="eval-logic learning-footprint">
      <summary>学习足迹 —— 早期练手项目（5 个，一行概览）</summary>
      <ul className="learning-list">
        {items.map((it) => (
          <li key={it.name}>
            <span className="learning-name">{it.name}</span>
            <span className="learning-desc">{it.desc}</span>
            {it.github && (
              <a
                className="learning-github"
                href={it.github}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => {
                  e.preventDefault()
                  const win = window.open(it.github, '_blank')
                  if (!win) window.location.href = it.github
                }}
              >
                GitHub ↗
              </a>
            )}
          </li>
        ))}
      </ul>
    </details>
  )
}

export default function App() {
  const [projects, setProjects] = useState([])
  const [resume, setResume] = useState('')
  const [active, setActive] = useState(null)
  const [view, setView] = useState('home') // 'home' | 'projects' | 'about'
  const [evalReport, setEvalReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      fetchDataOrStatic('/api/projects', 'projects'),
      fetchDataOrStatic('/api/resume', 'resume'),
      fetch('/api/eval')
        .then((r) => (r.ok ? r.json() : Promise.resolve(null)))
        .catch(() => null),
    ])
      .then(([pj, rs, ev]) => {
        setProjects((pj?.items ?? pj) ?? [])
        setResume(rs ? (rs.body ?? rs) : '')
        setEvalReport(ev)
        setLoading(false)
      })
      .catch(() => {
        setError('页面数据加载失败，请检查网络或稍后重试。')
        setLoading(false)
      })
  }, [])

  const heroBlurb = useMemo(() => {
    if (!resume) return '一个页面，讲清楚我的项目与能力。'
    // 跳过 markdown 标题行（## xxx），列表行去掉 - / 数字等符号，拼成自然的一句话
    const first = resume
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l && !/^#{1,6}\s/.test(l))
      .slice(0, 2)
      .map((l) => l.replace(/^[-•*\d]+[.、]?\s*/, ''))
      .join('；')
    return first || '一个页面，讲清楚我的项目与能力。'
  }, [resume])

  const activeProject = active ? projects.find((p) => p.path === active) : null

  const openProjects = () => {
    setActive(null)
    setView('projects')
    window.scrollTo({ top: 0 })
  }
  const openAbout = () => {
    setActive(null)
    setView('about')
    window.scrollTo({ top: 0 })
  }
  const goHome = () => {
    setActive(null)
    setView('home')
    window.scrollTo({ top: 0 })
  }
  const goToBlock = (id) => {
    setActive(null)
    setView('home')
    setTimeout(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
    }, 60)
  }

  return (
    <div className="app">
      <header className="nav">
        <span className="logo" style={{ cursor: 'pointer' }} onClick={goHome}>我的作品集</span>
        <a className="nav-link" href="#projects" onClick={(e) => { e.preventDefault(); openProjects() }}>项目</a>
        {view === 'home' && (
          <>
            <a className="nav-link" href="#eval" onClick={(e) => { e.preventDefault(); goToBlock('eval') }}>评测门禁</a>
            <a className="nav-link" href="#about" onClick={(e) => { e.preventDefault(); openAbout() }}>关于我</a>
          </>
        )}
      </header>

      {view === 'home' && (
        <section className="hero">
          <div className="hero-inner">
            <p className="hero-kicker">应届 · 大模型应用全栈</p>
            <h1 className="hero-title">Ask My Resume</h1>
            <p className="hero-sub">{heroBlurb}</p>
            <div className="hero-cta">
              <button className="btn-primary" onClick={openProjects}>看我的项目</button>
              <button className="btn-ghost" onClick={openAbout}>关于我</button>
            </div>
          </div>
        </section>
      )}

      {view === 'projects' && (
        <section id="projects" className="section projects-view">
          <div className="section-head">
            <h2 className="section-title">项目</h2>
            <p className="section-sub">解决"简历放不完"的问题，把知识沉淀下来。</p>
          </div>

          {loading && <p className="state">加载中…</p>}
          {error && <p className="state error">{error}</p>}

        {activeProject ? (
          <ProjectDetail project={activeProject} onBack={() => setActive(null)} />
        ) : (
          <div className="grid">
            {projects.map((p) => (
              <ProjectCard key={p.path} project={p} onOpen={() => setActive(p.path)} />
            ))}
          </div>
        )}
        <LearningJourney />
          <div className="projects-back">
            <button className="btn-ghost" onClick={goHome}>← 返回首页</button>
          </div>
        </section>
      )}

      {view === 'about' && (
        <section className="section about-view">
          <ResumeDetail
            resume={resume}
            heroBlurb={heroBlurb}
            onBack={goHome}
            onProjects={openProjects}
          />
          <div className="projects-back">
            <button className="btn-ghost" onClick={goHome}>← 返回首页</button>
          </div>
        </section>
      )}

      {view === 'home' && (
        <>
          <EvalSection report={evalReport} />

          <section id="about" className="section about">
            <div className="section-head">
              <h2 className="section-title">关于我</h2>
              <p className="section-sub">应届 · 大模型应用全栈。点击进入完整介绍。</p>
            </div>
            {loading ? (
              <p className="state">加载中…</p>
            ) : (
              <div className="about-preview">
                <p className="about-body">{heroBlurb || '应届生，主攻大模型应用全栈。'}</p>
                <button className="btn-ghost" onClick={openAbout}>查看完整介绍 →</button>
              </div>
            )}
          </section>
        </>
      )}

      <footer className="footer">© 2026 · Ask My Resume</footer>
      <ChatWidget />
    </div>
  )
}