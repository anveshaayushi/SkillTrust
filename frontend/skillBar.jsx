import React from 'react'

export default function SkillBar({ label, value, max = 100, color = '#6C63FF', delay = 0 }) {
  const pct = Math.round((value / max) * 100)

  const barColor =
    pct >= 80 ? '#00D4AA' :
    pct >= 60 ? '#6C63FF' :
    pct >= 40 ? '#FFB800' : '#FF6B35'

  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 13, color: '#E8EAF0', fontFamily: 'DM Sans, sans-serif' }}>{label}</span>
        <span style={{ fontSize: 12, color: barColor, fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>
          {value}
        </span>
      </div>
      <div style={{ height: 6, background: '#252A35', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${pct}%`,
          background: `linear-gradient(90deg, ${barColor}99, ${barColor})`,
          borderRadius: 4,
          transition: `width 1s cubic-bezier(0.4,0,0.2,1) ${delay}s`,
        }} />
      </div>
    </div>
  )
}
