import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { FileText, CheckCircle, Loader2, AlertCircle, UploadCloud } from 'lucide-react'
import toast from 'react-hot-toast'

// We'll simulate upload progress for demo; replace with real API call
function simulateUpload(file, onProgress, onDone) {
  let p = 0
  const iv = setInterval(() => {
    p += Math.random() * 18
    if (p >= 100) {
      p = 100
      clearInterval(iv)
      onProgress(100)
      setTimeout(() => onDone({ job_id: 'job_demo', candidate_id: 'cand_001' }), 400)
    } else {
      onProgress(Math.round(p))
    }
  }, 200)
}

function FileItem({ file, status, progress, error }) {
  const iconColor =
    status === 'done'  ? '#00D4AA' :
    status === 'error' ? '#FF6B35' : '#6C63FF'

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 14,
      padding: '14px 18px',
      background: '#181C24', border: '1px solid #252A35', borderRadius: 12,
      marginBottom: 10,
    }}>
      <FileText size={20} color={iconColor} />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: '#E8EAF0', marginBottom: 6 }}>
          {file.name}
          <span style={{ marginLeft: 8, fontSize: 11, color: '#6B7280' }}>
            {(file.size / 1024).toFixed(1)} KB
          </span>
        </div>
        {status === 'uploading' && (
          <div style={{ height: 4, background: '#252A35', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{
              height: '100%', width: `${progress}%`,
              background: 'linear-gradient(90deg, #6C63FF, #00D4AA)',
              borderRadius: 2,
              transition: 'width 0.2s ease',
            }} />
          </div>
        )}
        {status === 'done'  && <div style={{ fontSize: 11, color: '#00D4AA' }}>✓ Uploaded — pipeline started</div>}
        {status === 'error' && <div style={{ fontSize: 11, color: '#FF6B35' }}>{error}</div>}
      </div>
      {status === 'uploading' && <Loader2 size={16} color="#6C63FF" style={{ animation: 'spin 1s linear infinite' }} />}
      {status === 'done'      && <CheckCircle size={16} color="#00D4AA" />}
      {status === 'error'     && <AlertCircle size={16} color="#FF6B35" />}
    </div>
  )
}

export default function UploadPage() {
  const nav = useNavigate()
  const [files, setFiles] = useState([]) // [{file, status, progress, error}]

  const onDrop = useCallback((accepted, rejected) => {
    rejected.forEach(r => toast.error(`${r.file.name}: ${r.errors[0]?.message}`))

    const newItems = accepted.map(f => ({ file: f, status: 'uploading', progress: 0, error: null }))
    setFiles(prev => [...prev, ...newItems])

    newItems.forEach((item, idx) => {
      simulateUpload(
        item.file,
        (p) => setFiles(prev => prev.map(f => f.file === item.file ? { ...f, progress: p } : f)),
        (result) => {
          setFiles(prev => prev.map(f => f.file === item.file ? { ...f, status: 'done', progress: 100 } : f))
          toast.success(`${item.file.name} queued for evaluation!`)
        }
      )
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'] },
    maxSize: 10 * 1024 * 1024,
  })

  const allDone = files.length > 0 && files.every(f => f.status === 'done')

  return (
    <div style={{ padding: '36px 40px', maxWidth: 700 }}>
      <h1 style={{ fontFamily: 'Syne, sans-serif', fontSize: 28, fontWeight: 800, color: '#E8EAF0', marginBottom: 8 }}>
        Upload Resumes
      </h1>
      <p style={{ color: '#6B7280', fontSize: 14, marginBottom: 32 }}>
        Upload PDF or TXT resumes. Each file triggers the full 5-agent evaluation pipeline.
      </p>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        style={{
          border: `2px dashed ${isDragActive ? '#6C63FF' : '#252A35'}`,
          borderRadius: 16,
          padding: '48px 32px',
          textAlign: 'center',
          cursor: 'pointer',
          background: isDragActive ? 'rgba(108,99,255,0.05)' : '#181C24',
          transition: 'all 0.2s ease',
          marginBottom: 24,
        }}
      >
        <input {...getInputProps()} />
        <div style={{ marginBottom: 16 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16,
            background: isDragActive ? 'rgba(108,99,255,0.2)' : '#252A35',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto', transition: 'all 0.2s',
          }}>
            <UploadCloud size={24} color={isDragActive ? '#6C63FF' : '#6B7280'} />
          </div>
        </div>
        <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 18, fontWeight: 700, color: '#E8EAF0', marginBottom: 8 }}>
          {isDragActive ? 'Drop to upload' : 'Drag & drop resumes here'}
        </div>
        <div style={{ fontSize: 13, color: '#6B7280' }}>
          or <span style={{ color: '#6C63FF', fontWeight: 600 }}>click to browse</span>
          &nbsp;· PDF or TXT · max 10MB each
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 12, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace', marginBottom: 12, letterSpacing: '0.06em' }}>
            UPLOAD QUEUE ({files.length})
          </div>
          {files.map((f, i) => <FileItem key={i} {...f} />)}
        </div>
      )}

      {/* Actions */}
      {allDone && (
        <button
          onClick={() => nav('/')}
          style={{
            width: '100%', padding: '14px',
            background: 'linear-gradient(135deg, #6C63FF, #00D4AA)',
            border: 'none', borderRadius: 12, cursor: 'pointer',
            fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 15, color: '#fff',
            letterSpacing: '0.02em',
          }}
        >
          View Dashboard →
        </button>
      )}

      {/* Info cards */}
      <div style={{ marginTop: 32, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        {[
          { label: 'Profile Agent', desc: 'Extracts skills, GitHub, experience' },
          { label: 'Authenticity Agent', desc: 'SAS score + fraud detection' },
          { label: 'Skill Testing Agent', desc: 'LLM coding tasks + Judge0' },
          { label: 'Resume Engine', desc: 'Before/after PDF report' },
        ].map(card => (
          <div key={card.label} style={{
            padding: '14px 16px',
            background: '#181C24', border: '1px solid #252A35', borderRadius: 10,
          }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#6C63FF', marginBottom: 4 }}>{card.label}</div>
            <div style={{ fontSize: 12, color: '#6B7280' }}>{card.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
