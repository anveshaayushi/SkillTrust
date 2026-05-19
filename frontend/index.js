/**
 * api/index.js
 * Connects to Person 1's FastAPI backend at /api/*
 * All agent results flow through these endpoints.
 */
import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// ─── Upload ───────────────────────────────────────────────────────────────────
/**
 * Upload a PDF/text resume.
 * Returns { job_id, candidate_id }
 */
export async function uploadResume(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await http.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// ─── Evaluation ───────────────────────────────────────────────────────────────
/**
 * Trigger full agent pipeline for a candidate.
 * Returns { job_id }
 */
export async function evaluateCandidate(candidateId) {
  const { data } = await http.post(`/evaluate/${candidateId}`)
  return data
}

/**
 * Poll job status. Returns { status, progress, result? }
 * status: 'pending' | 'running' | 'done' | 'error'
 */
export async function getJobStatus(jobId) {
  const { data } = await http.get(`/jobs/${jobId}`)
  return data
}

// ─── Candidates ───────────────────────────────────────────────────────────────
/**
 * List all evaluated candidates.
 * Returns [{ id, name, sas_score, fraud_flag, skill_score, ... }]
 */
export async function listCandidates() {
  const { data } = await http.get('/candidates')
  return data
}

/**
 * Get full evaluation result for one candidate.
 * Returns the full orchestrator state object.
 */
export async function getCandidate(candidateId) {
  const { data } = await http.get(`/candidates/${candidateId}`)
  return data
}

// ─── Resume Engine ────────────────────────────────────────────────────────────
/**
 * Get the before/after resume report as base64 PDF.
 * Returns { before_pdf_b64, after_pdf_b64, improvements: [] }
 */
export async function getResumeReport(candidateId) {
  const { data } = await http.get(`/candidates/${candidateId}/resume-report`)
  return data
}

/**
 * Download the final PDF report as a Blob.
 */
export async function downloadPDFReport(candidateId) {
  const response = await http.get(`/candidates/${candidateId}/download-pdf`, {
    responseType: 'blob',
  })
  return response.data
}

// ─── Agent Status Feed ────────────────────────────────────────────────────────
/**
 * Get current agent status feed.
 * Returns [{ agent, status, last_run, message }]
 */
export async function getAgentStatuses() {
  const { data } = await http.get('/agents/status')
  return data
}

// ─── SSE Stream ───────────────────────────────────────────────────────────────
/**
 * Subscribe to real-time job updates via Server-Sent Events.
 * Usage: const es = subscribeToJob(jobId, onMessage, onDone)
 *        es.close() to unsubscribe
 */
export function subscribeToJob(jobId, onMessage, onDone) {
  const es = new EventSource(`/api/jobs/${jobId}/stream`)
  es.onmessage = (e) => {
    const payload = JSON.parse(e.data)
    onMessage(payload)
    if (payload.status === 'done' || payload.status === 'error') {
      es.close()
      onDone?.(payload)
    }
  }
  es.onerror = () => es.close()
  return es
}

export default http
