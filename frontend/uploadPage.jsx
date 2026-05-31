import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'

import {
  FileText,
  CheckCircle,
  Loader2,
  AlertCircle,
  UploadCloud,
  Send
} from 'lucide-react'

import toast from 'react-hot-toast'


// ========================================
// SKILL KEY NORMALISER
// Mirrors _skill_for_agent() in orchestrator.py exactly
// ========================================

function toSkillKey(label) {
  const s = (label || '').trim().toLowerCase()
  if (['python', 'react', 'sql', 'ml', 'fastapi'].includes(s)) return s
  if (s.includes('sql'))                                          return 'sql'
  if (s.includes('machine') || s.includes('tensorflow') ||
      s.includes('pytorch') || s === 'ml')                       return 'ml'
  if (s.includes('react') || s.includes('next'))                 return 'react'
  if (s.includes('fastapi'))                                      return 'fastapi'
  if (s.includes('python') || s.includes('django') ||
      s.includes('flask'))                                        return 'python'
  return 'python'
}


// ========================================
// SKILL TEST BLOCK
// evalResult is LIFTED to parent to survive re-renders.
// Parent passes evalResult + setEvalResult so state persists
// even when evalOverrides triggers a parent re-render.
// ========================================

function SkillTestBlock({ skill, question, evidenceScore, onEvalComplete, evalResult, setEvalResult }) {
  const [answer,     setAnswer]     = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [evalError,  setEvalError]  = useState(null)

  const handleSubmit = async () => {
    if (!answer.trim()) {
      toast.error('Please write an answer before submitting.')
      return
    }
    setSubmitting(true)
    setEvalError(null)

    try {
      const payload = {
        skill,
        skill_key:        toSkillKey(skill),
        claimed_level:    'intermediate',
        evidence:         evidenceScore ?? 0.0,
        task_description: question,
        answer:           answer.trim(),
      }

      const response = await fetch('http://127.0.0.1:8000/evaluate', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data?.detail || `Server error ${response.status}`)
      }

      setEvalResult(data)        // lifted — survives parent re-render
      onEvalComplete(skill, data)

      const label =
        data.verdict === 'Pass'    ? '✅ Passed!' :
        data.verdict === 'Partial' ? '⚠️ Partial pass' : '❌ Failed'
      toast(label, { icon: '' })

    } catch (err) {
      const msg = err.message || 'Evaluation failed'
      setEvalError(msg)
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  const verdictColor =
    evalResult?.verdict === 'Pass'    ? '#00D4AA' :
    evalResult?.verdict === 'Partial' ? '#FFB800' : '#FF6B35'

  return (
    <div>
      {/* Question box */}
      <div style={{
        marginTop: 6, padding: '8px 10px',
        background: '#1a1f2e', borderRadius: 8,
        fontSize: 12, color: '#E8EAF0',
        lineHeight: 1.5, whiteSpace: 'pre-wrap',
      }}>
        {question}
      </div>

      {/* Answer textarea + submit — hidden after evaluation */}
      {!evalResult && (
        <div style={{ marginTop: 8 }}>
          <textarea
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            placeholder="Write your answer here…"
            rows={5}
            style={{
              width: '100%', boxSizing: 'border-box',
              background: '#0f1219', border: '1px solid #252A35',
              borderRadius: 8, color: '#E8EAF0', fontSize: 12,
              fontFamily: 'JetBrains Mono, monospace', lineHeight: 1.6,
              padding: '10px 12px', resize: 'vertical', outline: 'none',
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={submitting}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              marginTop: 8, padding: '7px 16px',
              background: submitting ? '#252A35' : 'linear-gradient(135deg, #6C63FF, #00D4AA)',
              border: 'none', borderRadius: 8,
              cursor: submitting ? 'not-allowed' : 'pointer',
              fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 12,
              color: '#fff', letterSpacing: '0.02em',
            }}
          >
            {submitting
              ? <><Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> Evaluating…</>
              : <><Send size={12} /> Submit Answer</>
            }
          </button>
          {evalError && (
            <div style={{ marginTop: 6, fontSize: 11, color: '#FF6B35' }}>{evalError}</div>
          )}
        </div>
      )}

      {/* Evaluation result card */}
      {evalResult && (
        <div style={{
          marginTop: 10, padding: '12px 14px',
          background: '#0f1219',
          border: `1px solid ${verdictColor}33`,
          borderRadius: 10,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
            <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 800, fontSize: 18, color: verdictColor }}>
              {evalResult.verdict}
            </span>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: verdictColor, fontWeight: 700 }}>
              {evalResult.total}/100
            </span>
            <div style={{ display: 'flex', gap: 6, marginLeft: 4, flexWrap: 'wrap' }}>
              {[
                { label: 'Correctness',  val: evalResult.correctness  },
                { label: 'Completeness', val: evalResult.completeness },
                { label: 'Quality',      val: evalResult.code_quality },
                { label: 'Edge Cases',   val: evalResult.edge_cases   },
              ].map(d => (
                <span key={d.label} style={{
                  fontSize: 10, fontFamily: 'JetBrains Mono, monospace',
                  color: '#9CA3AF', background: '#181C24',
                  border: '1px solid #252A35', borderRadius: 4, padding: '2px 7px',
                }}>
                  {d.label} {d.val}/25
                </span>
              ))}
            </div>
          </div>
          {evalResult.strengths && (
            <div style={{ display: 'flex', gap: 6, marginBottom: 6, alignItems: 'flex-start' }}>
              <span style={{ fontSize: 10, color: '#00D4AA', fontFamily: 'JetBrains Mono, monospace', flexShrink: 0, paddingTop: 1 }}>STRENGTH</span>
              <span style={{ fontSize: 12, color: '#9CA3AF', lineHeight: 1.5 }}>{evalResult.strengths}</span>
            </div>
          )}
          {evalResult.improvements && (
            <div style={{ display: 'flex', gap: 6, alignItems: 'flex-start' }}>
              <span style={{ fontSize: 10, color: '#FFB800', fontFamily: 'JetBrains Mono, monospace', flexShrink: 0, paddingTop: 1 }}>IMPROVE</span>
              <span style={{ fontSize: 12, color: '#9CA3AF', lineHeight: 1.5 }}>{evalResult.improvements}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}


// ========================================
// API CALL
// ========================================

async function simulateUpload(
  file,
  candidateName,
  onProgress,
  onDone,
  onError
) {

  try {

    onProgress(15)

    const formData = new FormData()

    formData.append(
      "resume",
      file
    )

    // Send candidate name override if provided
    if (candidateName && candidateName.trim()) {
      formData.append("candidate_name", candidateName.trim())
    }

    onProgress(40)

    const response = await fetch(
      "http://127.0.0.1:8000/analyze",
      {
        method: "POST",
        body: formData,
      }
    )

    onProgress(65)

    const raw = await response.text()

    let data

    try {

      data = JSON.parse(raw)

    } catch {

      throw new Error(
        "Server returned invalid JSON"
      )
    }

    if (!response.ok) {

      const msg =

        data?.error?.message ||

        data?.detail ||

        `Backend request failed (${response.status})`

      throw new Error(msg)
    }

    if (data.success === false) {

      const msg =

        data?.error?.message ||

        "Analysis failed"

      throw new Error(msg)
    }

    console.log("BACKEND RESPONSE:")
    console.log(data)

    onProgress(100)

    onDone(data)

  } catch (err) {

    console.error(err)

    onError(
      err.message || "Upload failed"
    )
  }
}


// ========================================
// FILE ITEM
// ========================================

function FileItem({
  file,
  status,
  progress,
  error
}) {

  const iconColor =

    status === 'done'
      ? '#00D4AA'

      : status === 'error'
      ? '#FF6B35'

      : '#6C63FF'

  return (

    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,

        padding: '14px 18px',

        background: '#181C24',

        border:
          '1px solid #252A35',

        borderRadius: 12,

        marginBottom: 10,
      }}
    >

      <FileText
        size={20}
        color={iconColor}
      />

      <div style={{ flex: 1 }}>

        {/* FILE NAME */}

        <div
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: '#E8EAF0',
            marginBottom: 6,
          }}
        >

          {file.name}

          <span
            style={{
              marginLeft: 8,
              fontSize: 11,
              color: '#6B7280',
            }}
          >

            {(file.size / 1024).toFixed(1)} KB

          </span>

        </div>


        {/* PROGRESS BAR */}

        {status === 'uploading' && (

          <div
            style={{
              height: 4,
              background: '#252A35',
              borderRadius: 2,
              overflow: 'hidden',
            }}
          >

            <div
              style={{
                height: '100%',
                width: `${progress}%`,
                background:
                  'linear-gradient(90deg, #6C63FF, #00D4AA)',
                borderRadius: 2,
                transition: 'width 0.2s ease',
              }}
            />

          </div>
        )}


        {/* STATUS */}

        {status === 'done' && (

          <div
            style={{
              fontSize: 11,
              color: '#00D4AA',
            }}
          >
            ✓ Uploaded — pipeline completed
          </div>
        )}

        {status === 'error' && (

          <div
            style={{
              fontSize: 11,
              color: '#FF6B35',
            }}
          >
            {error}
          </div>
        )}

      </div>


      {/* ICONS */}

      {status === 'uploading' && (

        <Loader2
          size={16}
          color="#6C63FF"

          style={{
            animation:
              'spin 1s linear infinite'
          }}
        />
      )}

      {status === 'done' && (

        <CheckCircle
          size={16}
          color="#00D4AA"
        />
      )}

      {status === 'error' && (

        <AlertCircle
          size={16}
          color="#FF6B35"
        />
      )}

    </div>
  )
}


// ========================================
// MAIN PAGE
// ========================================

export default function UploadPage() {

  const nav = useNavigate()

  const [files,         setFiles]         = useState([])
  const [candidateName, setCandidateName] = useState('')

  // evalOverrides: { [fileIdx]: { [skill]: { score, passed, verdict } } }
  // evalResults:   { [fileIdx]: { [skill]: evalResultObject } }
  // Both are lifted up so SkillTestBlock state survives parent re-renders.
  const [evalOverrides, setEvalOverrides] = useState({})
  const [evalResults,   setEvalResults]   = useState({})

  const makeEvalCompleteHandler = (fileIndex) => (skill, evalData) => {
    setEvalOverrides(prev => ({
      ...prev,
      [fileIndex]: {
        ...(prev[fileIndex] || {}),
        [skill]: {
          passed:  evalData.verdict === 'Pass' || evalData.verdict === 'Partial',
          score:   `${evalData.total}/100`,
          verdict: evalData.verdict,
        },
      },
    }))
  }

  const makeSetEvalResult = (fileIndex, skill) => (data) => {
    setEvalResults(prev => ({
      ...prev,
      [fileIndex]: {
        ...(prev[fileIndex] || {}),
        [skill]: data,
      },
    }))
  }


  // ========================================
  // DROP HANDLER
  // ========================================

  const onDrop = useCallback(

    (accepted, rejected) => {

      rejected.forEach(r =>

        toast.error(
          `${r.file.name}: ${r.errors[0]?.message}`
        )
      )

      const newItems = accepted.map(f => ({
        file: f,
        status: 'uploading',
        progress: 0,
        error: null,
      }))

      setFiles(prev => [
        ...prev,
        ...newItems
      ])

      newItems.forEach((item) => {

        simulateUpload(

          item.file,

          candidateName,

          // PROGRESS
          (p) =>

            setFiles(prev =>

              prev.map(f =>

                f.file === item.file

                  ? {
                      ...f,
                      progress: p
                    }

                  : f
              )
            ),

          // SUCCESS
          (result) => {

            console.log(
              "FINAL RESULT:",
              result
            )

            setFiles(prev =>

              prev.map(f =>

                f.file === item.file

                  ? {
                      ...f,
                      status: 'done',
                      progress: 100,
                      result,
                    }

                  : f
              )
            )

            toast.success(
              `${item.file.name} analyzed successfully!`
            )
          },

          // ERROR
          (error) => {

            setFiles(prev =>

              prev.map(f =>

                f.file === item.file

                  ? {
                      ...f,
                      status: 'error',
                      error,
                    }

                  : f
              )
            )

            toast.error(error)
          }
        )
      })

    },

    [candidateName]   // ← must include candidateName so it's never stale
  )


  // Use a ref so the dropzone always calls the latest version of onDrop
  // without needing to re-create the dropzone instance.
  const onDropRef = React.useRef(onDrop)
  React.useEffect(() => { onDropRef.current = onDrop }, [onDrop])

  // ========================================
  // DROPZONE
  // ========================================

  const {
    getRootProps,
    getInputProps,
    isDragActive
  } = useDropzone({

    onDrop: (accepted, rejected) => onDropRef.current(accepted, rejected),

    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },

    maxSize: 10 * 1024 * 1024,
  })


  const allDone =

    files.length > 0 &&

    files.every(
      f => f.status === 'done'
    )


  // ========================================
  // UI
  // ========================================

  return (

    <div
      style={{
        padding: '36px 40px',
        maxWidth: 700,
      }}
    >

      {/* HEADER */}

      <h1
        style={{
          fontFamily:
            'Syne, sans-serif',

          fontSize: 28,

          fontWeight: 800,

          color: '#E8EAF0',

          marginBottom: 8,
        }}
      >
        Upload Resumes
      </h1>

      <p
        style={{
          color: '#6B7280',
          fontSize: 14,
          marginBottom: 32,
        }}
      >
        Upload PDF, TXT, or DOCX resumes.
        Each file triggers the full
        AI evaluation pipeline.
      </p>


      {/* CANDIDATE NAME INPUT + DROPZONE — combined card */}

      <div style={{
        background: '#181C24', border: '1px solid #252A35',
        borderRadius: 16, padding: '24px', marginBottom: 24,
      }}>

        {/* Name field */}
        <div style={{ marginBottom: 20 }}>
          <div style={{
            fontSize: 10, color: '#6B7280',
            fontFamily: 'JetBrains Mono, monospace',
            letterSpacing: '0.1em', marginBottom: 8,
          }}>
            CANDIDATE NAME <span style={{ color: '#4B5563' }}>(optional — overrides extracted name)</span>
          </div>
          <input
            type="text"
            value={candidateName}
            onChange={e => setCandidateName(e.target.value)}
            placeholder="e.g. Rohan Sharma"
            style={{
              width: '100%', boxSizing: 'border-box',
              background: '#0f1219',
              border: '1px solid #252A35', borderRadius: 10,
              color: '#E8EAF0', fontSize: 14,
              fontFamily: 'DM Sans, sans-serif',
              padding: '12px 16px', outline: 'none',
              transition: 'border-color 0.2s',
            }}
            onFocus={e => e.target.style.borderColor = '#6C63FF'}
            onBlur={e  => e.target.style.borderColor = '#252A35'}
          />
        </div>

        {/* Divider */}
        <div style={{ borderTop: '1px solid #252A35', marginBottom: 20 }} />

        {/* Dropzone */}
        <div
          {...getRootProps()}
          style={{
            border: `2px dashed ${isDragActive ? '#6C63FF' : '#2A3040'}`,
            borderRadius: 12, padding: '40px 32px', textAlign: 'center',
            cursor: 'pointer', background: isDragActive ? 'rgba(108,99,255,0.05)' : 'transparent',
            transition: 'all 0.2s ease',
          }}
        >

          <input {...getInputProps()} />

          <div style={{ marginBottom: 14 }}>
            <div style={{
              width: 52, height: 52, borderRadius: 14,
              background: isDragActive ? 'rgba(108,99,255,0.2)' : '#252A35',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto', transition: 'all 0.2s',
            }}>
              <UploadCloud size={22} color={isDragActive ? '#6C63FF' : '#6B7280'} />
            </div>
          </div>

          <div style={{
            fontFamily: 'Syne, sans-serif', fontSize: 17, fontWeight: 700,
            color: '#E8EAF0', marginBottom: 6,
          }}>
            {isDragActive ? 'Drop to upload' : 'Drag & drop resume here'}
          </div>
          <div style={{ fontSize: 13, color: '#6B7280' }}>
            or{' '}
            <span style={{ color: '#6C63FF', fontWeight: 600 }}>click to browse</span>
            {' '}· PDF, TXT, or DOCX · max 10 MB
          </div>

        </div>

      </div>

      {/* Hidden — old dropzone div removed, logic moved above */}
      {false && <div />}

      {/* FILE LIST */}

      {files.length > 0 && (

        <div style={{ marginBottom: 24 }}>

          <div
            style={{
              fontSize: 12,

              color: '#6B7280',

              fontFamily:
                'JetBrains Mono, monospace',

              marginBottom: 12,

              letterSpacing: '0.06em',
            }}
          >

            UPLOAD QUEUE ({files.length})

          </div>

          {files.map((f, i) => (

            <FileItem
              key={i}
              {...f}
            />

          ))}


          {/* ANALYSIS RESULTS */}

          {files.map((f, idx) => (

            f.result && (f.result.authenticity || f.result.profile) && (

              <div
                key={idx}
                style={{
                  background: '#181C24',
                  border: '1px solid #252A35',
                  borderRadius: 14,
                  padding: '20px 22px',
                  marginTop: 16,
                  color: 'white',
                }}
              >

                {/* ── CANDIDATE IDENTITY ── */}
                <div style={{ marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid #252A35' }}>
                  <div style={{
                    fontFamily: 'Syne, sans-serif', fontSize: 20, fontWeight: 800,
                    color: '#E8EAF0', marginBottom: 4,
                  }}>
                    {f.result?.name || f.result?.profile?.name || f.file.name.replace(/\.[^.]+$/, '')}
                  </div>
                  <div style={{ fontSize: 13, color: '#6B7280' }}>
                    {f.result?.role || f.result?.profile?.title || ''}
                    {f.result?.authenticity?.trust_level && (
                      <span style={{
                        marginLeft: 12, fontSize: 11, fontWeight: 600,
                        fontFamily: 'JetBrains Mono, monospace',
                        color:
                          f.result.authenticity.trust_level === 'High'   ? '#00D4AA' :
                          f.result.authenticity.trust_level === 'Medium' ? '#FFB800' : '#FF6B35',
                      }}>
                        {f.result.authenticity.trust_level.toUpperCase()} TRUST
                      </span>
                    )}
                  </div>
                </div>

                {/* ── SCORES ROW ── */}
                <div style={{
                  display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: 12, marginBottom: 20,
                }}>
                  {[
                    { label: 'AUTH SCORE', value: Math.round((f.result?.authenticity?.authenticity_score || 0) * 100), color: '#6C63FF' },
                    { label: 'SKILL SCORE', value: f.result?.skill_score || 0, color: '#FFB800' },
                    { label: 'OVERALL', value: f.result?.overall_score || 0, color: '#00D4AA' },
                  ].map(s => (
                    <div key={s.label} style={{
                      background: '#0f1219', borderRadius: 10,
                      padding: '12px 14px', border: '1px solid #252A35',
                    }}>
                      <div style={{
                        fontSize: 9, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace',
                        letterSpacing: '0.1em', marginBottom: 6,
                      }}>{s.label}</div>
                      <div style={{
                        fontFamily: 'Syne, sans-serif', fontSize: 28,
                        fontWeight: 800, color: s.color, lineHeight: 1,
                      }}>{s.value}</div>
                    </div>
                  ))}
                </div>

                {/* ── SKILL GROUPS ── */}
                {Array.isArray(f.result?.skill_results) && f.result.skill_results.length > 0 && (() => {
                  const verified = f.result.skill_results.filter(r => r.category === 'verified' || r.score === 'Verified')
                  const pending  = f.result.skill_results.filter(r => r.category === 'pending'  || r.score === 'Pending' || r.score === 'Error')

                  return (
                    <div style={{ marginBottom: 20 }}>

                      {/* Verified skills */}
                      {verified.length > 0 && (
                        <div style={{ marginBottom: 14 }}>
                          <div style={{
                            fontSize: 9, color: '#00D4AA', fontFamily: 'JetBrains Mono, monospace',
                            letterSpacing: '0.1em', marginBottom: 8,
                          }}>
                            ✓ VERIFIED SKILLS ({verified.length})
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                            {verified.map(r => (
                              <span key={r.skill} style={{
                                fontSize: 11, padding: '3px 10px', borderRadius: 20,
                                background: 'rgba(0,212,170,0.1)',
                                border: '1px solid rgba(0,212,170,0.3)',
                                color: '#00D4AA',
                                fontFamily: 'JetBrains Mono, monospace',
                              }}>{r.skill}</span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Pending skills summary chips */}
                      {pending.length > 0 && (
                        <div style={{ marginBottom: 14 }}>
                          <div style={{
                            fontSize: 9, color: '#FFB800', fontFamily: 'JetBrains Mono, monospace',
                            letterSpacing: '0.1em', marginBottom: 8,
                          }}>
                            ◎ UNVERIFIED — TEST REQUIRED ({pending.length})
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                            {pending.map(r => {
                              const override   = evalOverrides?.[idx]?.[r.skill]
                              const liveScore  = override?.score ?? r.score
                              const verdictCol = override
                                ? (override.verdict === 'Pass'    ? '#00D4AA' :
                                   override.verdict === 'Partial' ? '#FFB800' : '#FF6B35')
                                : '#FFB800'
                              return (
                                <span key={r.skill} style={{
                                  fontSize: 11, padding: '3px 10px', borderRadius: 20,
                                  background: override ? `${verdictCol}18` : 'rgba(255,184,0,0.1)',
                                  border: `1px solid ${verdictCol}44`,
                                  color: verdictCol,
                                  fontFamily: 'JetBrains Mono, monospace',
                                }}>
                                  {r.skill}
                                  <span style={{ marginLeft: 6, fontWeight: 700 }}>{liveScore}</span>
                                </span>
                              )
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })()}

                {/* ── QUESTIONS — only for unverified/pending skills ── */}
                {Array.isArray(f.result?.skill_results) && f.result.skill_results.some(r => f.result.skill_questions?.[r.skill]) && (
                  <div style={{ borderTop: '1px solid #252A35', paddingTop: 16 }}>
                    <div style={{
                      fontSize: 9, color: '#6B7280', fontFamily: 'JetBrains Mono, monospace',
                      letterSpacing: '0.1em', marginBottom: 14,
                    }}>
                      SKILL ASSESSMENTS
                    </div>

                    {f.result.skill_results
                      .filter(entry => f.result.skill_questions?.[entry.skill])
                      .map((entry, si) => {
                        const question    = f.result.skill_questions[entry.skill]
                        const override    = evalOverrides?.[idx]?.[entry.skill]
                        const liveScore   = override?.score ?? entry.score
                        const scoreColor  = override
                          ? (override.verdict === 'Pass'    ? '#00D4AA' :
                             override.verdict === 'Partial' ? '#FFB800' : '#FF6B35')
                          : '#FFB800'

                        return (
                          <div key={entry.skill} style={{ marginBottom: 20 }}>
                            {/* Skill header row */}
                            <div style={{
                              display: 'flex', alignItems: 'center', gap: 8,
                              marginBottom: 8,
                            }}>
                              <span style={{ fontSize: 13, color: '#E8EAF0', fontWeight: 600 }}>
                                {entry.skill}
                              </span>
                              {entry.difficulty && entry.difficulty !== '—' && (
                                <span style={{
                                  fontSize: 10, color: '#6B7280',
                                  fontFamily: 'JetBrains Mono, monospace',
                                  border: '1px solid #252A35', borderRadius: 4, padding: '1px 6px',
                                }}>
                                  {entry.difficulty}
                                </span>
                              )}
                              <span style={{ marginLeft: 'auto', fontWeight: 700, fontSize: 12, color: scoreColor }}>
                                {liveScore}
                              </span>
                            </div>

                            <SkillTestBlock
                              skill={entry.skill}
                              question={question}
                              evidenceScore={f.result?.evidence?.aggregated_skill_scores?.[entry.skill] ?? 0.0}
                              onEvalComplete={makeEvalCompleteHandler(idx)}
                              evalResult={evalResults?.[idx]?.[entry.skill] ?? null}
                              setEvalResult={makeSetEvalResult(idx, entry.skill)}
                            />
                          </div>
                        )
                      })
                    }
                  </div>
                )}

              </div>

            )

          ))}


          {allDone && (

            <button

              onClick={() => nav('/')}

              style={{
                width: '100%',

                marginTop: 20,

                padding: '14px',

                background:
                  'linear-gradient(135deg, #6C63FF, #00D4AA)',

                border: 'none',

                borderRadius: 12,

                cursor: 'pointer',

                fontFamily:
                  'Syne, sans-serif',

                fontWeight: 700,

                fontSize: 15,

                color: '#fff',

                letterSpacing: '0.02em',
              }}
            >

              View Dashboard →

            </button>

          )}

        </div>
      )}

    </div>
  )
}
