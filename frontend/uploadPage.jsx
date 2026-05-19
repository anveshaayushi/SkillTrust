import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'

import {
  FileText,
  CheckCircle,
  Loader2,
  AlertCircle,
  UploadCloud
} from 'lucide-react'

import toast from 'react-hot-toast'


// ========================================
// API CALL
// ========================================

async function simulateUpload(
  file,
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

  const [files, setFiles] = useState([])


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

    []
  )


  // ========================================
  // DROPZONE
  // ========================================

  const {
    getRootProps,
    getInputProps,
    isDragActive
  } = useDropzone({

    onDrop,

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


      {/* DROPZONE */}

      <div

        {...getRootProps()}

        style={{

          border:
            `2px dashed ${
              isDragActive
                ? '#6C63FF'
                : '#252A35'
            }`,

          borderRadius: 16,

          padding: '48px 32px',

          textAlign: 'center',

          cursor: 'pointer',

          background:

            isDragActive
              ? 'rgba(108,99,255,0.05)'
              : '#181C24',

          transition:
            'all 0.2s ease',

          marginBottom: 24,
        }}
      >

        <input {...getInputProps()} />

        <div style={{ marginBottom: 16 }}>

          <div
            style={{
              width: 56,
              height: 56,

              borderRadius: 16,

              background:

                isDragActive
                  ? 'rgba(108,99,255,0.2)'
                  : '#252A35',

              display: 'flex',

              alignItems: 'center',

              justifyContent: 'center',

              margin: '0 auto',

              transition:
                'all 0.2s',
            }}
          >

            <UploadCloud
              size={24}

              color={
                isDragActive
                  ? '#6C63FF'
                  : '#6B7280'
              }
            />

          </div>

        </div>

        <div
          style={{
            fontFamily:
              'Syne, sans-serif',

            fontSize: 18,

            fontWeight: 700,

            color: '#E8EAF0',

            marginBottom: 8,
          }}
        >

          {isDragActive
            ? 'Drop to upload'
            : 'Drag & drop resumes here'}

        </div>

        <div
          style={{
            fontSize: 13,
            color: '#6B7280',
          }}
        >

          or{" "}

          <span
            style={{
              color: '#6C63FF',
              fontWeight: 600,
            }}
          >
            click to browse
          </span>

          &nbsp;· PDF, TXT, or DOCX · max 10MB each

        </div>

      </div>


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

                  border:
                    '1px solid #252A35',

                  borderRadius: 12,

                  padding: 20,

                  marginTop: 16,

                  color: 'white',
                }}
              >

                {/* FILE NAME */}

                <h3
                  style={{
                    fontSize: 18,
                    fontWeight: 700,
                    marginBottom: 12,
                  }}
                >
                  {f.file.name}
                </h3>


                {/* TRUST BADGE */}

                <div
                  style={{
                    display: 'inline-block',

                    padding: '6px 12px',

                    borderRadius: 999,

                    background:

                      f.result?.authenticity
                        ?.trust_level === 'High'

                        ? 'rgba(0,212,170,0.15)'

                        : f.result?.authenticity
                            ?.trust_level === 'Medium'

                        ? 'rgba(255,184,0,0.15)'

                        : 'rgba(255,107,53,0.15)',

                    color:

                      f.result?.authenticity
                        ?.trust_level === 'High'

                        ? '#00D4AA'

                        : f.result?.authenticity
                            ?.trust_level === 'Medium'

                        ? '#FFB800'

                        : '#FF6B35',

                    fontWeight: 700,

                    fontSize: 13,

                    marginBottom: 12,
                  }}
                >

                  {
                    f.result?.authenticity
                      ?.trust_level || 'Unknown'
                  } Trust

                </div>


                {/* SCORE */}

                <p style={{ marginBottom: 8 }}>

                  <strong>
                    Authenticity Score:
                  </strong>{" "}

                  {
                    f.result?.authenticity
                      ?.authenticity_score
                  }

                </p>


                {/* SCORE BAR */}

                <div
                  style={{
                    height: 8,

                    background: '#252A35',

                    borderRadius: 999,

                    overflow: 'hidden',

                    marginTop: 8,

                    marginBottom: 16,
                  }}
                >

                  <div
                    style={{
                      width:
                        `${
                          (
                            f.result?.authenticity
                              ?.authenticity_score || 0
                          ) * 100
                        }%`,

                      height: '100%',

                      background:
                        'linear-gradient(90deg, #6C63FF, #00D4AA)',
                    }}
                  />

                </div>


                {/* FRAUD FLAG */}

                <p style={{ marginBottom: 12 }}>

                  <strong>
                    Fraud Flag:
                  </strong>{" "}

                  {
                    f.result?.authenticity
                      ?.fraud_flag

                      ? "YES"

                      : "NO"
                  }

                </p>


                {/* SKILLS */}

                <p
                  style={{
                    fontWeight: 700,
                    marginBottom: 8,
                  }}
                >
                  Skills:
                </p>

                <ul
                  style={{
                    paddingLeft: 20,
                    color: '#C9D1D9',
                  }}
                >

                  {(f.result?.profile?.skills || []).map(
                    (skill, i) => (

                      <li key={i}>
                        {skill}
                      </li>
                    )
                  )}

                </ul>


                {/* MISSING EVIDENCE */}

                <p
                  style={{
                    fontWeight: 700,
                    marginTop: 16,
                    marginBottom: 8,
                  }}
                >
                  Missing Evidence:
                </p>

                <ul
                  style={{
                    paddingLeft: 20,
                    color: '#FFB800',
                  }}
                >

                  {(f.result?.authenticity?.missing_skills || []).map(
                    (skill, i) => (

                      <li key={i}>
                        {skill}
                      </li>
                    )
                  )}

                </ul>


                {/* EVIDENCE SUMMARY */}

                {(f.result?.evidence?.github_links?.length > 0 ||

                  f.result?.evidence?.linkedin_links?.length > 0 ||

                  Object.keys(f.result?.evidence?.aggregated_skill_scores || {}).length > 0 ||

                  (f.result?.evidence?.project_snippets || []).length > 0) && (

                  <div style={{ marginTop: 16 }}>

                    <p
                      style={{
                        fontWeight: 700,
                        marginBottom: 8,
                      }}
                    >
                      Evidence
                    </p>

                    {(f.result?.evidence?.github_links || []).length > 0 && (

                      <p style={{ fontSize: 12, color: '#6B7280', marginBottom: 4 }}>

                        <strong style={{ color: '#C9D1D9' }}>GitHub:</strong>{" "}

                        {(f.result.evidence.github_links || []).join(", ")}

                      </p>

                    )}

                    {(f.result?.evidence?.linkedin_links || []).length > 0 && (

                      <p style={{ fontSize: 12, color: '#6B7280', marginBottom: 4 }}>

                        <strong style={{ color: '#C9D1D9' }}>LinkedIn:</strong>{" "}

                        {(f.result.evidence.linkedin_links || []).join(", ")}

                      </p>

                    )}

                    {Object.keys(f.result?.evidence?.aggregated_skill_scores || {}).length > 0 && (

                      <p style={{ fontSize: 12, color: '#6B7280', marginBottom: 4 }}>

                        <strong style={{ color: '#C9D1D9' }}>Evidence skills:</strong>{" "}

                        {JSON.stringify(f.result.evidence.aggregated_skill_scores)}

                      </p>

                    )}

                    {f.result?.evidence?.error && (

                      <p style={{ fontSize: 12, color: '#FF6B35' }}>

                        Evidence note: {String(f.result.evidence.error)}

                      </p>

                    )}

                  </div>

                )}


                {/* SKILL TESTING */}

                {Array.isArray(f.result?.skill_testing) && f.result.skill_testing.length > 0 && (

                  <div style={{ marginTop: 16 }}>

                    <p
                      style={{
                        fontWeight: 700,
                        marginBottom: 8,
                      }}
                    >
                      Skill checks
                    </p>

                    <ul
                      style={{
                        paddingLeft: 20,
                        color: '#6B7280',
                        fontSize: 12,
                        fontFamily: 'JetBrains Mono, monospace',
                      }}
                    >

                      {f.result.skill_testing.map((entry, si) => {

                        if (!entry || typeof entry !== "object") {

                          return (

                            <li key={si} style={{ marginBottom: 6 }}>

                              (invalid entry)

                            </li>

                          )

                        }

                        const key = Object.keys(entry)[0] || `item-${si}`

                        const val = entry[key]

                        return (

                          <li key={si} style={{ marginBottom: 6 }}>

                            {key}:{" "}

                            {typeof val === "object" && val !== null

                              ? (val?.status === "error"

                                  ? `Error — ${val?.error || "unknown"}`

                                  : "Completed")

                              : String(val)}

                          </li>

                        )

                      })}

                    </ul>

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