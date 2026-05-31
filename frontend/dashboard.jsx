import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, AlertTriangle, TrendingUp, Loader2, Upload, RefreshCw, Github } from 'lucide-react'
import StatusBadge from './statusBadge'

const ALL_AGENTS = [
  { key: 'profile_agent',       label: 'Profile',    color: '#6C63FF' },
  { key: 'evidence_agent',      label: 'Evidence',   color: '#00D4AA' },
  { key: 'authenticity_agent',  label: 'Auth',       color: '#FFB800' },
  { key: 'skill_testing_agent', label: 'Skill Test', color: '#FF6B35' },
  { key: 'score_aggregator',    label: 'Aggregator', color: '#9CA3AF' },
  { key: 'github_ai_agent',     label: 'GitHub AI',  color: '#8B5CF6' },
]

function AgentBadge({ agentKey, ran = true }) {
  const meta = ALL_AGENTS.find(a => a.key === agentKey) || { label: agentKey, color: '#6B7280' }
  return (
    <span style={{
      fontSize: 9, fontFamily: 'JetBrains Mono, monospace',
      color:      ran ? meta.color : '#3A3F4B',
      background: ran ? `${meta.color}18` : 'transparent',
      border:     `1px solid ${ran ? meta.color + '44' : '#2A2F3A'}`,
      borderRadius: 4, padding: '2px 6px', whiteSpace: 'nowrap',
    }}>
      {meta.label}
    </span>
  )
}

function StatCard({ icon: Icon, label, value, sub, color = '#6C63FF' }) {
  return (
    <div style={{
      background: '#181C24', border: '1px solid #252A35', borderRadius: 16,
      padding: '24px 26px', display: 'flex', flexDirection: 'column', gap: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          width: 40, height: 40, borderRadius: 12, background: `${color}18`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <Icon size={18} color={color} />
        </div>
        <span style={{ fontSize: 12, color: '#6B7280', fontFamily: 'DM Sans, sans-serif', fontWeight: 500 }}>
          {label}
        </span>
      </div>
      <div style={{
        fontFamily: 'Syne, sans-serif', fontSize: 36, fontWeight: 800,
        color: '#E8EAF0', lineHeight: 1, paddingLeft: 4,
      }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 12, color: '#6B7280', paddingLeft: 4, lineHeight: 1.4 }}>{sub}</div>}
    </div>
  )
}

function CandidateRow({ c, onClick }) {
  const scoreColor =
    c.overall_score >= 80 ? '#00D4AA' :
    c.overall_score >= 60 ? '#6C63FF' :
    c.overall_score >= 40 ? '#FFB800' : '#FF6B35'
  const isRunning = c.status === 'RUNNING'
  const ghAI    = c.github_ai
  const ghProb  = ghAI?.overall_ai_probability ?? null
  const ghVerdict = ghAI?.overall_verdict ?? null
  const ghColor =
    ghProb === null ? '#4B5563' :
    ghProb >= 0.60  ? '#FF6B35' :
    ghProb >= 0.35  ? '#FFB800' : '#00D4AA'

  return (
    <div
      onClick={onClick}
      style={{ borderBottom: '1px solid #1E2230', cursor: !isRunning ? 'pointer' : 'default', transition: 'background 0.15s' }}
      onMouseEnter={e => { if (!isRunning) e.currentTarget.style.background = '#1A1F2C' }}
      onMouseLeave={e => { e.currentTarget.style.background = 'transparent' }}
    >
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 90px 90px 90px 120px 150px 70px',
        alignItems: 'center', gap: 16, padding: '16px 24px',
      }}>
        <div>
          <div style={{ fontWeight: 700, color: '#E8EAF0', fontSize: 14, marginBottom: 3 }}>
            {c.name && c.name !== 'Unknown' ? c.name : '—'}
          </div>
          <div style={{ fontSize: 12, color: '#6B7280' }}>
            {c.role && c.role !== 'Unknown Role' ? c.role : 'Role unknown'}
          </div>
        </div>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, color: scoreColor, fontWeight: 600 }}>
          {isRunning ? '—' : c.sas_score}
        </div>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, color: '#E8EAF0' }}>
          {isRunning ? '—' : c.skill_score}
        </div>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 16, color: scoreColor, fontWeight: 700 }}>
          {isRunning
            ? <Loader2 size={14} color="#FFB800" style={{ animation: 'spin 1s linear infinite' }} />
            : c.overall_score}
        </div>
        <div>
          {c.fraud_flag
            ? <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 10,
                fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: '#FFB800',
                background: 'rgba(255,184,0,0.12)', border: '1px solid rgba(255,184,0,0.35)',
                borderRadius: 6, padding: '3px 8px',
              }}>⚠ UNVERIFIED</span>
            : isRunning ? <StatusBadge variant="running" /> : <StatusBadge variant="done" />
          }
        </div>
        <div>
          {ghVerdict && ghVerdict !== 'No GitHub links found' && ghVerdict !== 'Analysis unavailable' && ghVerdict !== 'Could not access repositories'
            ? <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 9,
                fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: ghColor,
                background: `${ghColor}18`, border: `1px solid ${ghColor}44`,
                borderRadius: 6, padding: '3px 7px',
              }}>
                <Github size={9} />
                {ghProb !== null ? `${Math.round(ghProb * 100)}% AI` : ghVerdict}
              </span>
            : <span style={{ fontSize: 10, color: '#3A3F4B', fontFamily: 'JetBrains Mono, monospace' }}>No GitHub</span>
          }
        </div>
        <div style={{ fontSize: 12, color: '#6C63FF', fontWeight: 600, textAlign: 'right' }}>
          {!isRunning ? 'View →' : ''}
        </div>
      </div>

      {/* All 6 agents — greyed out if didn't run */}
      <div style={{ paddingLeft: 24, paddingBottom: 12, display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 9, color: '#3A3F4B', fontFamily: 'JetBrains Mono, monospace', marginRight: 4, letterSpacing: '0.06em' }}>
          AGENTS:
        </span>
        {ALL_AGENTS.map(a => (
          <AgentBadge key={a.key} agentKey={a.key} ran={(c.agent_trace || []).includes(a.key)} />
        ))}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const nav = useNavigate()
  const [candidates, setCandidates] = useState([])
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState(null)

  const fetchCandidates = useCallback(async (showLoader = false) => {
    if (showLoader) setLoading(true)
    setError(null)
    try {
      const res  = await fetch('http://127.0.0.1:8000/candidates')
      const data = await res.json()
      if (data.success && Array.isArray(data.candidates)) setCandidates(data.candidates)
    } catch { setError('Cannot reach backend — is the server running?') }
    finally  { setLoading(false) }
  }, [])

  useEffect(() => { fetchCandidates(true) },  [fetchCandidates])
  useEffect(() => {
    const t = setInterval(() => fetchCandidates(false), 8000)
    return () => clearInterval(t)
  }, [fetchCandidates])

  const evaluated = candidates.filter(c => c.status !== 'RUNNING')
  const running   = candidates.filter(c => c.status === 'RUNNING')
  const flagged   = candidates.filter(c => c.fraud_flag)
  const avgScore  = evaluated.length
    ? Math.round(evaluated.reduce((s, c) => s + (c.overall_score || 0), 0) / evaluated.length) : 0
  const topC     = [...evaluated].sort((a, b) => (b.overall_score||0) - (a.overall_score||0))[0]
  const topScore = topC?.overall_score ?? 0
  const topSub   = topC
    ? [topC.name !== 'Unknown' ? topC.name : null, topC.role !== 'Unknown Role' ? topC.role : null]
        .filter(Boolean).join(' — ') || 'Candidate'
    : '—'

  return (
    <div style={{ padding: '36px 44px', width: '100%', boxSizing: 'border-box', minHeight: '100vh' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 40 }}>
        <div>
          <h1 style={{ fontFamily: 'Syne, sans-serif', fontSize: 32, fontWeight: 800, color: '#E8EAF0', marginBottom: 8, lineHeight: 1 }}>
            Evaluation Dashboard
          </h1>
          <p style={{ color: '#6B7280', fontSize: 14, margin: 0 }}>
            Real-time candidate pipeline
            {evaluated.length > 0 && ` — ${evaluated.length} evaluated`}
            {running.length  > 0 && `, ${running.length} in progress`}
          </p>
        </div>
        <button
          onClick={() => fetchCandidates(true)}
          style={{
            display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px',
            background: '#181C24', border: '1px solid #252A35', borderRadius: 10,
            color: '#9CA3AF', cursor: 'pointer', fontSize: 12,
            fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.04em', transition: 'all 0.2s',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = '#6C63FF'; e.currentTarget.style.color = '#6C63FF' }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = '#252A35'; e.currentTarget.style.color = '#9CA3AF' }}
        >
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 20, marginBottom: 40 }}>
        <StatCard icon={Users}         label="Total Candidates" value={candidates.length}              sub="uploaded this session"  color="#6C63FF" />
        <StatCard icon={TrendingUp}    label="Avg Score"        value={evaluated.length ? avgScore : '—'} sub="across evaluated"   color="#00D4AA" />
        <StatCard icon={AlertTriangle} label="Unverified"       value={flagged.length}                 sub="require manual review"  color="#FF6B35" />
        <StatCard icon={TrendingUp}    label="Top Score"        value={topScore || '—'}                sub={topSub}                 color="#FFB800" />
      </div>

      {loading && (
        <div style={{ background: '#181C24', border: '1px solid #252A35', borderRadius: 16, padding: '80px 20px', textAlign: 'center' }}>
          <Loader2 size={32} color="#6C63FF" style={{ animation: 'spin 1s linear infinite', margin: '0 auto 16px', display: 'block' }} />
          <div style={{ color: '#6B7280', fontSize: 14 }}>Loading candidates…</div>
        </div>
      )}

      {!loading && error && (
        <div style={{ background: 'rgba(255,107,53,0.08)', border: '1px solid rgba(255,107,53,0.3)', borderRadius: 16, padding: '32px', textAlign: 'center' }}>
          <AlertTriangle size={24} color="#FF6B35" style={{ margin: '0 auto 12px', display: 'block' }} />
          <div style={{ color: '#FF6B35', fontSize: 14 }}>{error}</div>
        </div>
      )}

      {!loading && !error && candidates.length === 0 && (
        <div style={{ background: '#181C24', border: '1px solid #252A35', borderRadius: 16, padding: '80px 20px', textAlign: 'center' }}>
          <div style={{ color: '#6B7280', fontSize: 14, marginBottom: 20 }}>No candidates yet — upload a resume to get started.</div>
          <button onClick={() => nav('/upload')} style={{ padding: '12px 24px', background: 'linear-gradient(135deg, #6C63FF, #00D4AA)', border: 'none', borderRadius: 10, color: '#fff', cursor: 'pointer', fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 14 }}>
            Upload Resume
          </button>
        </div>
      )}

      {!loading && !error && candidates.length > 0 && (
        <div style={{ background: '#181C24', border: '1px solid #252A35', borderRadius: 18, overflow: 'hidden' }}>
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 90px 90px 90px 120px 150px 70px',
            gap: 16, padding: '14px 24px', borderBottom: '1px solid #252A35', background: '#111318',
          }}>
            {['CANDIDATE', 'SAS', 'SKILL', 'OVERALL', 'STATUS', 'GITHUB AI', ''].map(h => (
              <div key={h} style={{ fontSize: 10, color: '#4B5563', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.08em' }}>{h}</div>
            ))}
          </div>
          {[...candidates]
            .sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0))
            .map(c => <CandidateRow key={c.id} c={c} onClick={() => c.status !== 'RUNNING' && nav(`/report/${c.id}`)} />)
          }
        </div>
      )}

      <div
        onClick={() => nav('/upload')}
        style={{
          marginTop: 24, padding: '18px 20px', border: '1px dashed #252A35', borderRadius: 14,
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
          cursor: 'pointer', color: '#6B7280', fontSize: 14, transition: 'all 0.2s',
        }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = '#6C63FF'; e.currentTarget.style.color = '#6C63FF' }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = '#252A35'; e.currentTarget.style.color = '#6B7280' }}
      >
        <Upload size={16} /> Add more resumes
      </div>
    </div>
  )
}
