import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Shared/Sidebar'
import Dashboard from './pages/Dashboard'
import UploadPage from './pages/UploadPage'
import CandidateReport from './pages/CandidateReport'
import AgentStatus from './pages/AgentStatus'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden mesh-bg">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/"           element={<Dashboard />} />
          <Route path="/upload"     element={<UploadPage />} />
          <Route path="/report/:id" element={<CandidateReport />} />
          <Route path="/agents"     element={<AgentStatus />} />
        </Routes>
      </main>
    </div>
  )
}
