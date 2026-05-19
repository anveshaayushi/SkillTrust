import React from 'react'

const VARIANTS = {
  done:    { label: 'DONE',    bg: 'rgba(0,212,170,0.12)',  border: '#00D4AA', color: '#00D4AA' },
  running: { label: 'RUNNING', bg: 'rgba(255,184,0,0.12)',  border: '#FFB800', color: '#FFB800' },
  pending: { label: 'PENDING', bg: 'rgba(107,114,128,0.12)',border: '#6B7280', color: '#6B7280' },
  error:   { label: 'ERROR',   bg: 'rgba(255,107,53,0.12)', border: '#FF6B35', color: '#FF6B35' },
  fraud:   { label: '⚠ FRAUD', bg: 'rgba(255,107,53,0.15)', border: '#FF6B35', color: '#FF6B35' },
  hire:    { label: '✓ HIRE',  bg: 'rgba(0,212,170,0.12)',  border: '#00D4AA', color: '#00D4AA' },
  reject:  { label: '✕ REJECT',bg: 'rgba(255,107,53,0.12)', border: '#FF6B35', color: '#FF6B35' },
  healthy: { label: '● LIVE',  bg: 'rgba(0,212,170,0.12)',  border: '#00D4AA', color: '#00D4AA' },
}

export default function StatusBadge({ variant = 'pending', label: overrideLabel }) {
  const v = VARIANTS[variant] || VARIANTS.pending
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 20,
      border: `1px solid ${v.border}`,
      background: v.bg,
      color: v.color,
      fontFamily: 'JetBrains Mono, monospace',
      fontSize: 10,
      fontWeight: 500,
      letterSpacing: '0.05em',
    }}>
      {overrideLabel || v.label}
    </span>
  )
}
