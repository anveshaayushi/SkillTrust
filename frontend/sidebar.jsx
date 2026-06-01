import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Upload, FileText, Activity, Zap
} from 'lucide-react'

const NAV = [
  { to: '/',       label: 'Dashboard',   icon: LayoutDashboard },
  { to: '/upload', label: 'Upload',      icon: Upload },
  { to: '/agents', label: 'Agent Feed',  icon: Activity },
]

export default function Sidebar() {
  const loc = useLocation()

  return (
    <aside
      style={{
        width: 220,
        minWidth: 220,
        background: '#111318',
        borderRight: '1px solid #252A35',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 0',
        zIndex: 10,
      }}
    >
      {/* Logo */}
      <div style={{ padding: '0 20px 32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 10,
            background: 'linear-gradient(135deg, #6C63FF, #00D4AA)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Zap size={18} color="#fff" />
          </div>
          <div>
            <div style={{ fontFamily: 'Syne, sans-serif', fontWeight: 800, fontSize: 15, color: '#E8EAF0', lineHeight: 1 }}>
              TalentLens
            </div>
            <div style={{ fontSize: 10, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace', marginTop: 2 }}>
              v1.0 · Person 5
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '0 12px', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {NAV.map(({ to, label, icon: Icon }) => {
          const active = loc.pathname === to || (to !== '/' && loc.pathname.startsWith(to))
          return (
            <NavLink
              key={to}
              to={to}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 12px',
                borderRadius: 10,
                textDecoration: 'none',
                fontFamily: 'DM Sans, sans-serif',
                fontSize: 14,
                fontWeight: active ? 600 : 400,
                color: active ? '#E8EAF0' : '#6B7280',
                background: active ? 'rgba(108,99,255,0.12)' : 'transparent',
                border: active ? '1px solid rgba(108,99,255,0.25)' : '1px solid transparent',
                transition: 'all 0.2s ease',
              }}
            >
              <Icon size={16} color={active ? '#6C63FF' : '#6B7280'} />
              {label}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div style={{ padding: '16px 20px', borderTop: '1px solid #252A35' }}>
        <div style={{ fontSize: 11, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace', lineHeight: 1.6 }}>
          <div style={{ color: '#00D4AA', marginBottom: 4 }}>● AGENTS ONLINE</div>
          <div>FastAPI · localhost:8000</div>
        </div>
      </div>
    </aside>
  )
}
