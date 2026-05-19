import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import ScoreRing from './scoreRing'
import SkillBar from './skillBar'
import StatusBadge from './statusBadge'
import { MOCK_CANDIDATE_DETAIL } from './mockData'
import { generatePDF } from './pdfGenerator'
import toast from 'react-hot-toast'

// Section wrapper
function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{
        fontSize: 10, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace',
        letterSpacing: '0.1em', marginBottom: 14,
      }}>
        {title}
      </div>
      {children}
    </div>
  )
}

// Card
function Card({ children, style = {} }) {
  return (
    <div style={{
      background: '#181C24', border: '1px solid #252A35', borderRadius: 14,
      padding: '20px 22px', ...style,
    }}>
      {children}
    </div>
  )
}

// Skill test result row
function SkillTestRow({ result }) {
  const color = result.passed ? '#00D4AA' : '#FF6B35'
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '10px 0', borderBottom: '1px solid #252A35',
    }}>
      {result.passed
        ? <CheckCircle size={15} color="#00D4AA" />
        : <XCircle size={15} color="#FF6B35" />
      }
      <div style={{ flex: 1 }}>
        <span style={{ fontSize: 13, color: '#E8EAF0', fontWeight: 500 }}>{result.skill}</span>
        <span style={{
          marginLeft: 8, fontSize: 10, color: '#6B7280',
          fontFamily: 'JetBrains Mono, monospace',
          border: '1px solid #252A35', borderRadius: 4, padding: '1px 6px',
        }}>
          {result.difficulty}
        </span>
      </div>
      <span style={{
        fontFamily: 'JetBrains Mono, monospace', fontWeight: 700,
        fontSize: 14, color,
      }}>{result.score}</span>
    </div>
  )
}

// Resume improvement row
function ImprovementRow({ item, index }) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '100px 1fr 1fr', gap: 16,
      padding: '12px 0', borderBottom: '1px solid #252A35',
      animation: `slideUp 0.4s ease ${index * 0.08}s both`,
    }}>
      <div style={{
        fontSize: 11, fontWeight: 600, color: '#6C63FF',
        fontFamily: 'JetBrains Mono, monospace', paddingTop: 2,
      }}>{item.section}</div>
      <div>
        <div style={{ fontSize: 10, color: '#FF6B35', marginBottom: 4 }}>BEFORE</div>
        <div style={{ fontSize: 12, color: '#9CA3AF', lineHeight: 1.5 }}>{item.issue}</div>
      </div>
      <div>
        <div style={{ fontSize: 10, color: '#00D4AA', marginBottom: 4 }}>AFTER</div>
        <div style={{ fontSize: 12, color: '#E8EAF0', lineHeight: 1.5 }}>{item.fix}</div>
      </div>
    </div>
  )
}

export default function CandidateReport() {
  const { id } = useParams()
  const nav = useNavigate()
  const [downloading, setDownloading] = useState(false)

  // In production: fetch from API using id
  const c = MOCK_CANDIDATE_DETAIL

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await generatePDF(c)
      toast.success('PDF downloaded!')
    } catch (e) {
      toast.error('PDF generation failed')
    } finally {
      setDownloading(false)
    }
  }

  const scoreColor =
    c.overall_score >= 80 ? '#00D4AA' :
    c.overall_score >= 60 ? '#6C63FF' : '#FF6B35'

  return (
    <div style={{ padding: '36px 40px', maxWidth: 1050 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20, marginBottom: 32 }}>
        <button
          onClick={() => nav('/')}
          style={{
            display: 'flex', alignItems: 'center', gap: 6, padding: '8px 12px',
            background: '#181C24', border: '1px solid #252A35', borderRadius: 8,
            color: '#6B7280', cursor: 'pointer', fontSize: 13, flexShrink: 0,
          }}
        >
          <ArrowLeft size={14} /> Back
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 6 }}>
            <h1 style={{ fontFamily: 'Syne, sans-serif', fontSize: 26, fontWeight: 800, color: '#E8EAF0' }}>
              {c.name}
            </h1>
            <StatusBadge variant={c.recommendation === 'HIRE' ? 'hire' : 'reject'} />
            {c.fraud_flag && <StatusBadge variant="fraud" />}
          </div>
          <div style={{ fontSize: 14, color: '#6B7280' }}>
            {c.role} · {c.location} · {c.email}
          </div>
        </div>
        <button
          onClick={handleDownload}
          disabled={downloading}
          style={{
            display: 'flex', alignItems: 'center', gap: 8, padding: '12px 20px',
            background: downloading ? '#252A35' : 'linear-gradient(135deg, #6C63FF, #00D4AA)',
            border: 'none', borderRadius: 10, cursor: downloading ? 'not-allowed' : 'pointer',
            fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 13, color: '#fff',
          }}
        >
          <Download size={15} />
          {downloading ? 'Generating…' : 'Download PDF'}
        </button>
      </div>

      {/* Score overview */}
      <Card style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 32 }}>
        <ScoreRing score={c.overall_score} size={100} strokeWidth={8} color="auto" label="Overall" />
        <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 20 }}>
          {[
            { label: 'Profile Score',    score: c.profile_score,  color: '#00D4AA' },
            { label: 'SAS Score',        score: c.sas_score,      color: '#6C63FF' },
            { label: 'Skill Score',      score: c.skill_score,    color: '#FFB800' },
          ].map(s => (
            <div key={s.label}>
              <div style={{ fontSize: 11, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace', marginBottom: 6, letterSpacing: '0.06em' }}>
                {s.label.toUpperCase()}
              </div>
              <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 36, fontWeight: 800, color: s.color, lineHeight: 1 }}>
                {s.score}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* 2-col layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        {/* SAS Breakdown */}
        <Card>
          <Section title="SAS SCORE BREAKDOWN">
            {Object.entries(c.sas_breakdown).map(([key, val], i) => (
              <SkillBar
                key={key}
                label={key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                value={val}
                delay={i * 0.1}
              />
            ))}
          </Section>
          {c.fraud_flag && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8, marginTop: 8,
              padding: '10px 14px', background: 'rgba(255,107,53,0.1)',
              borderRadius: 8, border: '1px solid rgba(255,107,53,0.3)',
            }}>
              <AlertTriangle size={14} color="#FF6B35" />
              <span style={{ fontSize: 12, color: '#FF6B35' }}>
                Fraud confidence: {(c.fraud_confidence * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </Card>

        {/* Skill test results */}
        <Card>
          <Section title="SKILL TESTING RESULTS">
            {c.skill_results.map(r => <SkillTestRow key={r.skill} result={r} />)}
          </Section>
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            {c.skills_matched.map(s => (
              <span key={s} style={{
                fontSize: 11, padding: '3px 10px', borderRadius: 20,
                background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.3)',
                color: '#00D4AA', fontFamily: 'JetBrains Mono, monospace',
              }}>{s}</span>
            ))}
          </div>
        </Card>
      </div>

      {/* Resume Engine — Before / After */}
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={{ fontSize: 10, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.1em' }}>
            RESUME ENGINE — IMPROVEMENTS
          </div>
          <div style={{ display: 'flex', gap: 16, fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}>
            <span style={{ color: '#FF6B35' }}>■ BEFORE</span>
            <span style={{ color: '#00D4AA' }}>■ AFTER</span>
          </div>
        </div>

        {/* Column headers */}
        <div style={{
          display: 'grid', gridTemplateColumns: '100px 1fr 1fr', gap: 16,
          paddingBottom: 10, borderBottom: '1px solid #252A35',
        }}>
          {['SECTION', 'ORIGINAL ISSUE', 'AI-IMPROVED VERSION'].map(h => (
            <div key={h} style={{ fontSize: 10, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.06em' }}>
              {h}
            </div>
          ))}
        </div>

        {c.resume_improvements.map((item, i) => (
          <ImprovementRow key={item.section} item={item} index={i} />
        ))}
      </Card>
    </div>
  )
}
