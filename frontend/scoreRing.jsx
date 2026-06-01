import React from 'react'

/**
 * ScoreRing
 * Animated circular score indicator.
 * Props: score (0-100), size, strokeWidth, color
 */
export default function ScoreRing({
  score = 0,
  size = 80,
  strokeWidth = 6,
  color = '#6C63FF',
  label,
}) {
  const r = (size - strokeWidth) / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ

  const scoreColor =
    score >= 80 ? '#00D4AA' :
    score >= 60 ? '#6C63FF' :
    score >= 40 ? '#FFB800' : '#FF6B35'

  const c = color === 'auto' ? scoreColor : color

  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Track */}
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke="#252A35" strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none"
          stroke={c}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{
            transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)',
          }}
        />
      </svg>
      {/* Centre text */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        gap: 2,
      }}>
        <span style={{
          fontFamily: 'Syne, sans-serif',
          fontWeight: 800,
          fontSize: size * 0.22,
          color: c,
          lineHeight: 1,
        }}>{score}</span>
        {label && (
          <span style={{ fontSize: size * 0.12, color: '#6B7280', fontFamily: 'DM Sans, sans-serif' }}>
            {label}
          </span>
        )}
      </div>
    </div>
  )
}
