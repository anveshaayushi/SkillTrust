/**
 * useJob.js
 * Custom hook to poll a job's status until done.
 * Switches to SSE (Server-Sent Events) if available.
 */
import { useState, useEffect, useRef } from 'react'
import { getJobStatus, subscribeToJob } from '../api'

export function useJob(jobId) {
  const [status, setStatus]   = useState('pending')
  const [progress, setProgress] = useState(0)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState(null)
  const esRef = useRef(null)

  useEffect(() => {
    if (!jobId) return

    // Try SSE first
    try {
      esRef.current = subscribeToJob(
        jobId,
        (payload) => {
          setStatus(payload.status)
          setProgress(payload.progress ?? 0)
          if (payload.result) setResult(payload.result)
        },
        (final) => {
          if (final.status === 'error') setError(final.message)
        }
      )
    } catch {
      // Fallback to polling
      const iv = setInterval(async () => {
        try {
          const data = await getJobStatus(jobId)
          setStatus(data.status)
          setProgress(data.progress ?? 0)
          if (data.result) { setResult(data.result); clearInterval(iv) }
          if (data.status === 'error') { setError(data.message); clearInterval(iv) }
        } catch (e) {
          setError(e.message)
          clearInterval(iv)
        }
      }, 2000)
      return () => clearInterval(iv)
    }

    return () => esRef.current?.close()
  }, [jobId])

  return { status, progress, result, error }
}
