import React, { useState, useEffect } from 'react'
import { Activity, RefreshCw } from 'lucide-react'
import StatusBadge from '../components/Shared/StatusBadge'
import { MOCK_AGENT_STATUSES } from '../api/mockData'

function AgentCard({ agent }) {
  return (
    <div style={{
      background: '#181C24', border: '1px solid #252A35', borderRadius: 14,
      padding: '20px 22px', display: 'flex', alignItems: 'center', gap: 20,
    }} className="stagger-child">
      {/* Color dot */}
      <div style={{
        width: 10, height: 10, borderRadius: '50%',
        background: agent.color, flexShrink: 0,
        boxShadow: `0 0 10px ${agent.color}88`,
      }} />
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
          <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 15, color: '#E8EAF0' }}>
            {agent.agent}
          </span>
          <StatusBadge variant={agent.status} />
        </div>
        <div style={{ fontSize: 13, color: '#6B7280' }}>{agent.message}</div>
      </div>
      <div style={{ textAlign: 'right' }}>
        <div style={{ fontSize: 11, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace' }}>
          LAST RUN
        </div>
        <div style={{ fontSize: 13, color: '#E8EAF0', fontFamily: 'JetBrains Mono, monospace', marginTop: 2 }}>
          {agent.last_run}
        </div>
      </div>
    </div>
  )
}

// Fake live log lines
const LOG_LINES = [
  { ts: '13:42:01', agent: 'Orchestrator', msg: 'Received job for candidate Kiran Patel', color: '#6C63FF' },
  { ts: '13:42:01', agent: 'Profile+Evidence', msg: 'Starting PDF extraction…', color: '#00D4AA' },
  { ts: '13:42:03', agent: 'Profile+Evidence', msg: 'Extracted 7 skills, found 3 GitHub repos', color: '#00D4AA' },
  { ts: '13:42:04', agent: 'Auth+Scoring', msg: 'Running difflib pipeline on code samples…', color: '#FF6B35' },
  { ts: '13:42:07', agent: 'Auth+Scoring', msg: 'cosine_similarity=0.82 — no fraud detected', color: '#FF6B35' },
  { ts: '13:42:08', agent: 'Skill Testing', msg: 'Generating React task (difficulty: Hard)…', color: '#FFB800' },
  { ts: '13:42:09', agent: 'Skill Testing', msg: 'Submitting to Judge0 for execution…', color: '#FFB800' },
  { ts: '13:42:12', agent: 'Orchestrator', msg: 'SAS score ready. Routing to Resume Engine…', color: '#6C63FF' },
]

export default function AgentStatus() {
  const [agents] = useState(MOCK_AGENT_STATUSES)
  const [visibleLogs, setVisibleLogs] = useState([])
  const [logIdx, setLogIdx] = useState(0)

  useEffect(() => {
    if (logIdx >= LOG_LINES.length) return
    const t = setTimeout(() => {
      setVisibleLogs(prev => [...prev, LOG_LINES[logIdx]])
      setLogIdx(i => i + 1)
    }, 600)
    return () => clearTimeout(t)
  }, [logIdx])

  const replay = () => { setVisibleLogs([]); setLogIdx(0) }

  return (
    <div style={{ padding: '36px 40px', maxWidth: 900 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontFamily: 'Syne, sans-serif', fontSize: 28, fontWeight: 800, color: '#E8EAF0', marginBottom: 6 }}>
            Agent Status Feed
          </h1>
          <p style={{ color: '#6B7280', fontSize: 14 }}>Live status of all 5 agents in the pipeline</p>
        </div>
        <button
          onClick={replay}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '10px 16px',
            background: '#181C24', border: '1px solid #252A35', borderRadius: 10,
            color: '#6B7280', cursor: 'pointer', fontSize: 13,
          }}
        >
          <RefreshCw size={14} /> Replay logs
        </button>
      </div>

      {/* Agent cards */}
      <div style={{ display: 'grid', gap: 12, marginBottom: 36 }}>
        {agents.map(a => <AgentCard key={a.agent} agent={a} />)}
      </div>

      {/* Live log terminal */}
      <div style={{
        background: '#0A0C10', border: '1px solid #252A35', borderRadius: 14,
        overflow: 'hidden',
      }}>
        {/* Terminal header */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '12px 16px', borderBottom: '1px solid #252A35',
          background: '#111318',
        }}>
          <div style={{ display: 'flex', gap: 6 }}>
            {['#FF5F57','#FFBD2E','#28CA41'].map(c => (
              <div key={c} style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />
            ))}
          </div>
          <span style={{ fontSize: 12, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace', marginLeft: 8 }}>
            pipeline.log
          </span>
          <div style={{ marginLeft: 'auto' }}>
            <Activity size={14} color="#00D4AA" />
          </div>
        </div>

        {/* Log lines */}
        <div style={{ padding: '16px', minHeight: 220, fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
          {visibleLogs.map((l, i) => (
            <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 8, animation: 'fadeIn 0.3s ease' }}>
              <span style={{ color: '#3D4455', flexShrink: 0 }}>{l.ts}</span>
              <span style={{ color: l.color, flexShrink: 0, minWidth: 130 }}>[{l.agent}]</span>
              <span style={{ color: '#A0AAB4' }}>{l.msg}</span>
            </div>
          ))}
          {logIdx < LOG_LINES.length && (
            <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
              <span style={{ color: '#6C63FF' }}>▋</span>
            </div>
          )}
          {logIdx >= LOG_LINES.length && (
            <div style={{ color: '#00D4AA', marginTop: 8 }}>✓ All agents nominal. Awaiting next job.</div>
          )}
        </div>
      </div>
    </div>
  )
}
