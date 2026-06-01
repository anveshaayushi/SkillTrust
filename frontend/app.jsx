import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './sidebar'
import Dashboard from './dashboard'
import UploadPage from './uploadPage'
import CandidateReport from './candidateReport'
import AgentStatus from './agentStatus'

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
