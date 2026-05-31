import React from 'react'
import { X, Github, GitCommit, FileCode, AlertTriangle, CheckCircle, Info } from 'lucide-react'

// ---------------------------------------------------------------------------
// Probability ring
// ---------------------------------------------------------------------------

function ProbRing({ probability, size = 80 }) {
  const r     = (size - 10) / 2
  const circ  = 2 * Math.PI * r
  const fill  = probability * circ
  const color =
    probability >= 0.60 ? '#FF6B35' :
    probability >= 0.35 ? '#FFB800' : '#00D4AA'

  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#252A35" strokeWidth={8} />
      <circle
        cx={size/2} cy={size/2} r={r}
        fill="none" stroke={color} strokeWidth={8}
        strokeDasharray={`${fill} ${circ}`}
        strokeLinecap="round"
        style={{ transition: 'stroke-dasharray 0.6s ease' }}
      />
      <text
        x={size/2} y={size/2}
        textAnchor="middle" dominantBaseline="central"
        fill={color}
        style={{ transform: 'rotate(90deg)', transformOrigin: `${size/2}px ${size/2}px`, fontFamily: 'Syne, sans-serif', fontWeight: 800, fontSize: size * 0.22 }}
      >
        {Math.round(probability * 100)}%
      </text>
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Signal row
// ---------------------------------------------------------------------------

function SignalRow({ signal, index }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 10,
      padding: '10px 0',
      borderBottom: '1px solid #1E2230',
      animation: `fadeIn 0.3s ease ${index * 0.05}s both`,
    }}>
      <AlertTriangle size={13} color="#FFB800" style={{ flexShrink: 0, marginTop: 2 }} />
      <span style={{ fontSize: 12, color: '#C9D1D9', lineHeight: 1.5 }}>{signal}</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Repo card
// ---------------------------------------------------------------------------

function RepoCard({ repo }) {
  const color =
    repo.ai_probability >= 0.60 ? '#FF6B35' :
    repo.ai_probability >= 0.35 ? '#FFB800' : '#00D4AA'

  const verdictIcon =
    repo.ai_probability >= 0.60 ? <AlertTriangle size={14} color="#FF6B35" /> :
    repo.ai_probability >= 0.35 ? <Info size={14} color="#FFB800" /> :
                                   <CheckCircle size={14} color="#00D4AA" />

  return (
    <div style={{
      background: '#0f1219',
      border: `1px solid ${color}33`,
      borderRadius: 12,
      padding: '16px 18px',
      marginBottom: 12,
    }}>
      {/* Repo header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        <ProbRing probability={repo.ai_probability} size={72} />
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            {verdictIcon}
            <a
              href={repo.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 14, fontWeight: 700, color: '#E8EAF0', textDecoration: 'none' }}
              onMouseEnter={e => e.target.style.color = '#6C63FF'}
              onMouseLeave={e => e.target.style.color = '#E8EAF0'}
            >
              {repo.repo}
            </a>
          </div>
          <div style={{ fontSize: 13, color: color, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: 8 }}>
            {repo.verdict}
          </div>
          {/* Meta pills */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {repo.commits !== undefined && (
              <span style={{
                display: 'flex', alignItems: 'center', gap: 4,
                fontSize: 10, fontFamily: 'JetBrains Mono, monospace',
                color: '#6B7280', background: '#181C24',
                border: '1px solid #252A35', borderRadius: 4, padding: '2px 7px',
              }}>
                <GitCommit size={9} />
                {repo.commits} commit{repo.commits !== 1 ? 's' : ''}
              </span>
            )}
            {repo.primary_language && repo.primary_language !== 'Unknown' && (
              <span style={{
                display: 'flex', alignItems: 'center', gap: 4,
                fontSize: 10, fontFamily: 'JetBrains Mono, monospace',
                color: '#6B7280', background: '#181C24',
                border: '1px solid #252A35', borderRadius: 4, padding: '2px 7px',
              }}>
                <FileCode size={9} />
                {repo.primary_language}
              </span>
            )}
            {repo.files_analysed !== undefined && (
              <span style={{
                fontSize: 10, fontFamily: 'JetBrains Mono, monospace',
                color: '#6B7280', background: '#181C24',
                border: '1px solid #252A35', borderRadius: 4, padding: '2px 7px',
              }}>
                {repo.files_analysed} file{repo.files_analysed !== 1 ? 's' : ''} analysed
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Signals */}
      {repo.signals && repo.signals.length > 0 && (
        <div>
          <div style={{
            fontSize: 9, color: '#4B5563', fontFamily: 'JetBrains Mono, monospace',
            letterSpacing: '0.08em', marginBottom: 6,
          }}>
            DETECTED SIGNALS
          </div>
          {repo.signals.map((s, i) => <SignalRow key={i} signal={s} index={i} />)}
        </div>
      )}

      {(!repo.signals || repo.signals.length === 0) && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '10px 12px', background: 'rgba(0,212,170,0.06)',
          border: '1px solid rgba(0,212,170,0.2)', borderRadius: 8,
        }}>
          <CheckCircle size={13} color="#00D4AA" />
          <span style={{ fontSize: 12, color: '#00D4AA' }}>No AI-authorship signals detected</span>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main modal
// ---------------------------------------------------------------------------

export default function GitHubAIModal({ data, onClose }) {
  if (!data) return null

  const overallColor =
    data.overall_ai_probability >= 0.60 ? '#FF6B35' :
    data.overall_ai_probability >= 0.35 ? '#FFB800' : '#00D4AA'

  const hasRepos = data.repos_analysed > 0

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
          zIndex: 1000,
        }}
      />

      {/* Panel */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0,
        width: 520, background: '#13161E',
        border: '1px solid #252A35', borderRight: 'none',
        zIndex: 1001, overflowY: 'auto',
        padding: '28px 28px',
        boxShadow: '-20px 0 60px rgba(0,0,0,0.5)',
        animation: 'slideInRight 0.25s ease',
      }}>

        {/* Close */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'rgba(139,92,246,0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Github size={18} color="#8B5CF6" />
            </div>
            <div>
              <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 16, fontWeight: 800, color: '#E8EAF0' }}>
                GitHub AI Analysis
              </div>
              <div style={{ fontSize: 11, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace' }}>
                {data.repos_analysed} repo{data.repos_analysed !== 1 ? 's' : ''} analysed
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              width: 32, height: 32, borderRadius: 8,
              background: '#252A35', border: 'none',
              cursor: 'pointer', color: '#6B7280',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
            onMouseEnter={e => e.currentTarget.style.background = '#313642'}
            onMouseLeave={e => e.currentTarget.style.background = '#252A35'}
          >
            <X size={14} />
          </button>
        </div>

        {/* No repos */}
        {!hasRepos && (
          <div style={{
            padding: '40px 20px', textAlign: 'center',
            background: '#181C24', border: '1px solid #252A35',
            borderRadius: 14,
          }}>
            <Github size={32} color="#4B5563" style={{ margin: '0 auto 12px', display: 'block' }} />
            <div style={{ fontSize: 14, color: '#6B7280', marginBottom: 6 }}>
              {data.overall_verdict || 'No GitHub repositories found'}
            </div>
            <div style={{ fontSize: 12, color: '#4B5563' }}>
              No GitHub links were found in this resume, or the repositories could not be accessed.
            </div>
          </div>
        )}

        {/* Overall summary */}
        {hasRepos && (
          <>
            <div style={{
              background: '#181C24', border: '1px solid #252A35',
              borderRadius: 14, padding: '20px 22px', marginBottom: 24,
              display: 'flex', alignItems: 'center', gap: 20,
            }}>
              <ProbRing probability={data.overall_ai_probability} size={90} />
              <div>
                <div style={{
                  fontSize: 9, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace',
                  letterSpacing: '0.1em', marginBottom: 6,
                }}>
                  OVERALL AI PROBABILITY
                </div>
                <div style={{
                  fontFamily: 'Syne, sans-serif', fontSize: 22,
                  fontWeight: 800, color: overallColor, lineHeight: 1, marginBottom: 8,
                }}>
                  {data.overall_verdict}
                </div>
                <div style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.5 }}>
                  Based on static code analysis across{' '}
                  <span style={{ color: '#E8EAF0' }}>{data.repos_analysed} repositor{data.repos_analysed !== 1 ? 'ies' : 'y'}</span>.
                  Heuristics check commit patterns, comment density, boilerplate signatures, and structural uniformity.
                </div>
              </div>
            </div>

            {/* What we check */}
            <div style={{
              background: 'rgba(108,99,255,0.06)', border: '1px solid rgba(108,99,255,0.2)',
              borderRadius: 10, padding: '12px 14px', marginBottom: 24,
            }}>
              <div style={{
                fontSize: 9, color: '#6C63FF', fontFamily: 'JetBrains Mono, monospace',
                letterSpacing: '0.08em', marginBottom: 8,
              }}>
                DETECTION METHODOLOGY
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {[
                  'Single-commit repos', 'Comment density', 'Boilerplate docstrings',
                  'Lazy exception handling', 'README over-structure', 'Uniform variable naming',
                  'Minimal file count', 'Perfect type hint coverage',
                ].map(m => (
                  <span key={m} style={{
                    fontSize: 10, fontFamily: 'JetBrains Mono, monospace',
                    color: '#9CA3AF', background: '#181C24',
                    border: '1px solid #252A35', borderRadius: 4, padding: '2px 7px',
                  }}>
                    {m}
                  </span>
                ))}
              </div>
            </div>

            {/* Per-repo breakdown */}
            <div style={{
              fontSize: 9, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace',
              letterSpacing: '0.1em', marginBottom: 12,
            }}>
              REPOSITORY BREAKDOWN
            </div>
            {data.repo_results.map((repo, i) => (
              <RepoCard key={i} repo={repo} />
            ))}

            {/* Disclaimer */}
            <div style={{
              marginTop: 20, padding: '12px 14px',
              background: '#181C24', border: '1px solid #252A35',
              borderRadius: 10,
            }}>
              <div style={{ fontSize: 11, color: '#4B5563', lineHeight: 1.6 }}>
                <span style={{ color: '#6B7280', fontWeight: 600 }}>Note:</span>{' '}
                These signals are heuristic indicators, not definitive proof of AI generation.
                A high score warrants further review — not automatic rejection.
                False positives can occur for clean, well-documented human code.
              </div>
            </div>
          </>
        )}

      </div>

      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0);   }
        }
      `}</style>
    </>
  )
}
