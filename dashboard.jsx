import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, AlertTriangle, TrendingUp, Loader2, Upload } from 'lucide-react'
import ScoreRing from '../components/Shared/ScoreRing'
import StatusBadge from '../components/Shared/StatusBadge'
import { MOCK_CANDIDATES, DASHBOARD_STATS } from '../api/mockData'

// Stat card
function StatCard({ icon: Icon, label, value, sub, color = '#6C63FF' }) {
  return (
    <div style={{
      background: '#181C24', border: '1px solid #252A35', borderRadius: 14,
      padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: 8,
    }} className="stagger-child">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          background: `${color}18`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={16} color={color} />
        </div>
        <span style={{ fontSize: 12, color: '#6B7280', fontFamily: 'DM Sans, sans-serif' }}>{label}</span>
      </div>
      <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 32, fontWeight: 800, color: '#E8EAF0', lineHeight: 1 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 12, color: '#6B7280' }}>{sub}</div>}
    </div>
  )
}

// Candidate row
function CandidateRow({ c, onClick }) {
  const scoreColor =
    c.overall_score >= 80 ? '#00D4AA' :
    c.overall_score >= 60 ? '#6C63FF' :
    c.overall_score >= 40 ? '#FFB800' : '#FF6B35'

  return (
    <div
      onClick={onClick}
      style={{
        display: 'grid', gridTemplateColumns: '1fr 100px 100px 100px 120px 80px',
        alignItems: 'center', gap: 16,
        padding: '14px 20px',
        borderBottom: '1px solid #252A35',
        cursor: 'pointer',
        transition: 'background 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = '#1E2230'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      {/* Name */}
      <div>
        <div style={{ fontWeight: 600, color: '#E8EAF0', fontSize: 14 }}>{c.name}</div>
        <div style={{ fontSize: 12, color: '#6B7280', marginTop: 2 }}>{c.role}</div>
      </div>
      {/* SAS */}
      <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, color: scoreColor, fontWeight: 600 }}>
        {c.status === 'running' ? '—' : c.sas_score}
      </div>
      {/* Skill */}
      <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, color: '#E8EAF0' }}>
        {c.status === 'running' ? '—' : c.skill_score}
      </div>
      {/* Overall */}
      <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 16, color: scoreColor, fontWeight: 700 }}>
        {c.status === 'running' ? (
          <Loader2 size={14} color="#FFB800" style={{ animation: 'spin 1s linear infinite' }} />
        ) : c.overall_score}
      </div>
      {/* Fraud */}
      <div>
        {c.fraud_flag
          ? <StatusBadge variant="fraud" />
          : c.status === 'running'
            ? <StatusBadge variant="running" />
            : <StatusBadge variant="done" />
        }
      </div>
      {/* Action */}
      <div style={{ fontSize: 12, color: '#6C63FF', fontWeight: 600, textAlign: 'right' }}>
        {c.status === 'done' ? 'View →' : ''}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const nav = useNavigate()
  const [candidates] = useState(MOCK_CANDIDATES)
  const stats = DASHBOARD_STATS

  return (
    <div style={{ padding: '36px 40px', maxWidth: 1100 }}>
      {/* Header */}
      <div style={{ marginBottom: 36 }}>
        <h1 style={{ fontFamily: 'Syne, sans-serif', fontSize: 28, fontWeight: 800, color: '#E8EAF0', marginBottom: 6 }}>
          Evaluation Dashboard
        </h1>
        <p style={{ color: '#6B7280', fontSize: 14 }}>
          Real-time candidate pipeline — {stats.done} evaluated, {stats.running} in progress
        </p>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 36 }}>
        <StatCard icon={Users}        label="Total Candidates" value={stats.total}     sub="uploaded this session"      color="#6C63FF" />
        <StatCard icon={TrendingUp}   label="Avg Score"        value={stats.avg_score} sub="across evaluated"           color="#00D4AA" />
        <StatCard icon={AlertTriangle}label="Fraud Flagged"    value={stats.flagged}   sub="require manual review"      color="#FF6B35" />
        <StatCard icon={TrendingUp}   label="Top Score"        value={stats.top_score} sub="Sneha Rao — Full Stack"     color="#FFB800" />
      </div>

      {/* Table */}
      <div style={{ background: '#181C24', border: '1px solid #252A35', borderRadius: 16, overflow: 'hidden' }}>
        {/* Table header */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 100px 100px 100px 120px 80px',
          gap: 16, padding: '12px 20px',
          borderBottom: '1px solid #252A35',
          background: '#111318',
        }}>
          {['CANDIDATE', 'SAS SCORE', 'SKILL', 'OVERALL', 'STATUS', ''].map(h => (
            <div key={h} style={{ fontSize: 10, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.08em' }}>
              {h}
            </div>
          ))}
        </div>

        {candidates.map(c => (
          <CandidateRow
            key={c.id}
            c={c}
            onClick={() => c.status === 'done' && nav(`/report/${c.id}`)}
          />
        ))}
      </div>

      {/* Upload CTA */}
      <div
        onClick={() => nav('/upload')}
        style={{
          marginTop: 20, padding: '16px 20px',
          border: '1px dashed #252A35', borderRadius: 12,
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
          cursor: 'pointer', color: '#6B7280', fontSize: 14,
          transition: 'all 0.2s',
        }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = '#6C63FF'; e.currentTarget.style.color = '#6C63FF' }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = '#252A35'; e.currentTarget.style.color = '#6B7280' }}
      >
        <Upload size={16} /> Add more resumes
      </div>
    </div>
  )
}
