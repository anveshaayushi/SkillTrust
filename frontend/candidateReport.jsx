import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Download,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Send,
  Loader2,
  Github,
} from "lucide-react";
import ScoreRing from "./scoreRing";
import SkillBar from "./skillBar";
import StatusBadge from "./statusBadge";
import GitHubAIModal from "./GitHubAIModal";
import { generatePDF } from "./pdfGenerator";
import toast from "react-hot-toast";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Map a raw skill label back to the normalised agent key.
 * Must mirror _skill_for_agent() in orchestrator.py exactly.
 */
function toSkillKey(label) {
  const s = (label || "").trim().toLowerCase();
  if (["python", "react", "sql", "ml", "fastapi"].includes(s)) return s;
  if (s.includes("sql")) return "sql";
  if (
    s.includes("machine") ||
    s.includes("tensorflow") ||
    s.includes("pytorch") ||
    s === "ml"
  )
    return "ml";
  if (s.includes("react") || s.includes("next")) return "react";
  if (s.includes("fastapi")) return "fastapi";
  if (s.includes("python") || s.includes("django") || s.includes("flask"))
    return "python";
  return "python";
}

// ---------------------------------------------------------------------------
// Sub-components (layout unchanged)
// ---------------------------------------------------------------------------

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div
        style={{
          fontSize: 10,
          color: "#6B7280",
          fontFamily: "JetBrains Mono, monospace",
          letterSpacing: "0.1em",
          marginBottom: 14,
        }}
      >
        {title}
      </div>
      {children}
    </div>
  );
}

function Card({ children, style = {} }) {
  return (
    <div
      style={{
        background: "#181C24",
        border: "1px solid #252A35",
        borderRadius: 14,
        padding: "20px 22px",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

// Skill test result row — unchanged visual, score text driven by state
function SkillTestRow({ result }) {
  const color = result.passed ? "#00D4AA" : "#FF6B35";
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "10px 0",
        borderBottom: "1px solid #252A35",
      }}
    >
      {result.passed ? (
        <CheckCircle size={15} color="#00D4AA" />
      ) : (
        <XCircle size={15} color="#FF6B35" />
      )}
      <div style={{ flex: 1 }}>
        <span style={{ fontSize: 13, color: "#E8EAF0", fontWeight: 500 }}>
          {result.skill}
        </span>
        <span
          style={{
            marginLeft: 8,
            fontSize: 10,
            color: "#6B7280",
            fontFamily: "JetBrains Mono, monospace",
            border: "1px solid #252A35",
            borderRadius: 4,
            padding: "1px 6px",
          }}
        >
          {result.difficulty}
        </span>
      </div>
      <span
        style={{
          fontFamily: "JetBrains Mono, monospace",
          fontWeight: 700,
          fontSize: 14,
          color,
        }}
      >
        {result.score}
      </span>
    </div>
  );
}

function ImprovementRow({ item, index }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "100px 1fr 1fr",
        gap: 16,
        padding: "12px 0",
        borderBottom: "1px solid #252A35",
        animation: `slideUp 0.4s ease ${index * 0.08}s both`,
      }}
    >
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: "#6C63FF",
          fontFamily: "JetBrains Mono, monospace",
          paddingTop: 2,
        }}
      >
        {item.section}
      </div>
      <div>
        <div style={{ fontSize: 10, color: "#FF6B35", marginBottom: 4 }}>
          BEFORE
        </div>
        <div style={{ fontSize: 12, color: "#9CA3AF", lineHeight: 1.5 }}>
          {item.issue}
        </div>
      </div>
      <div>
        <div style={{ fontSize: 10, color: "#00D4AA", marginBottom: 4 }}>
          AFTER
        </div>
        <div style={{ fontSize: 12, color: "#E8EAF0", lineHeight: 1.5 }}>
          {item.fix}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SkillTestBlock — question + answer input + submit + live eval result
// ---------------------------------------------------------------------------

/**
 * Renders the question box, answer textarea, submit button, and evaluation
 * feedback for a single skill. Sits between SkillTestRow and the next row,
 * exactly where the old read-only question block was.
 *
 * Props
 * -----
 * skill           : original skill label (e.g. "Machine Learning")
 * question        : task description string
 * evidenceScore   : 0.0–1.0, forwarded to backend for correct calibration
 * onEvalComplete  : (skill, evalResult) → void — called after successful eval
 */
function SkillTestBlock({
  skill,
  question,
  evidenceScore,
  candidateId,
  onEvalComplete,
  onScoresUpdated,
}) {
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [evalResult, setEvalResult] = useState(null);
  const [evalError, setEvalError] = useState(null);

  const handleSubmit = async () => {
    if (!answer.trim()) {
      toast.error("Please write an answer before submitting.");
      return;
    }
    setSubmitting(true);
    setEvalError(null);

    try {
      const payload = {
        skill,
        skill_key: toSkillKey(skill),
        claimed_level: "intermediate",
        evidence: evidenceScore ?? 0.0,
        task_description: question,
        answer: answer.trim(),
        candidate_id: candidateId || "", // ← persist to backend
      };

      const response = await fetch("http://127.0.0.1:8000/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok)
        throw new Error(data?.detail || `Server error ${response.status}`);

      setEvalResult(data);
      onEvalComplete(skill, data);

      // If backend returned updated scores, bubble them up to refresh header
      if (data.sas_score !== undefined && onScoresUpdated) {
        onScoresUpdated({
          sas_score: data.sas_score,
          skill_score: data.skill_score,
          overall_score: data.overall_score,
          sas_breakdown: data.sas_breakdown,
        });
      }

      const label =
        data.verdict === "Pass"
          ? "✅ Passed!"
          : data.verdict === "Partial"
            ? "⚠️ Partial pass"
            : "❌ Failed";
      toast(label, { icon: "" });
    } catch (err) {
      const msg = err.message || "Evaluation failed";
      setEvalError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const verdictColor =
    evalResult?.verdict === "Pass"
      ? "#00D4AA"
      : evalResult?.verdict === "Partial"
        ? "#FFB800"
        : "#FF6B35";

  return (
    <div style={{ marginLeft: 28, marginBottom: 10 }}>
      {/* Question box — same style as before */}
      <div
        style={{
          marginTop: 6,
          padding: "8px 10px",
          background: "#1a1f2e",
          borderRadius: 8,
          fontSize: 12,
          color: "#E8EAF0",
          lineHeight: 1.6,
          whiteSpace: "pre-wrap",
        }}
      >
        {question}
      </div>

      {/* Answer input — only shown while not yet evaluated */}
      {!evalResult && (
        <div style={{ marginTop: 8 }}>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Write your answer here…"
            rows={5}
            style={{
              width: "100%",
              boxSizing: "border-box",
              background: "#0f1219",
              border: "1px solid #252A35",
              borderRadius: 8,
              color: "#E8EAF0",
              fontSize: 12,
              fontFamily: "JetBrains Mono, monospace",
              lineHeight: 1.6,
              padding: "10px 12px",
              resize: "vertical",
              outline: "none",
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={submitting}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              marginTop: 8,
              padding: "7px 16px",
              background: submitting
                ? "#252A35"
                : "linear-gradient(135deg, #6C63FF, #00D4AA)",
              border: "none",
              borderRadius: 8,
              cursor: submitting ? "not-allowed" : "pointer",
              fontFamily: "Syne, sans-serif",
              fontWeight: 700,
              fontSize: 12,
              color: "#fff",
              letterSpacing: "0.02em",
            }}
          >
            {submitting ? (
              <>
                <Loader2
                  size={12}
                  style={{ animation: "spin 1s linear infinite" }}
                />{" "}
                Evaluating…
              </>
            ) : (
              <>
                <Send size={12} /> Submit Answer
              </>
            )}
          </button>
          {evalError && (
            <div style={{ marginTop: 6, fontSize: 11, color: "#FF6B35" }}>
              {evalError}
            </div>
          )}
        </div>
      )}

      {/* Evaluation result — shown after submit */}
      {evalResult && (
        <div
          style={{
            marginTop: 10,
            padding: "12px 14px",
            background: "#0f1219",
            border: `1px solid ${verdictColor}33`,
            borderRadius: 10,
          }}
        >
          {/* Verdict + score row */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              marginBottom: 10,
            }}
          >
            <span
              style={{
                fontFamily: "Syne, sans-serif",
                fontWeight: 800,
                fontSize: 18,
                color: verdictColor,
              }}
            >
              {evalResult.verdict}
            </span>
            <span
              style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: 13,
                color: verdictColor,
                fontWeight: 700,
              }}
            >
              {evalResult.total}/100
            </span>

            {/* Dimensional breakdown chips */}
            <div
              style={{
                display: "flex",
                gap: 6,
                marginLeft: 4,
                flexWrap: "wrap",
              }}
            >
              {[
                { label: "Correctness", val: evalResult.correctness },
                { label: "Completeness", val: evalResult.completeness },
                { label: "Quality", val: evalResult.code_quality },
                { label: "Edge Cases", val: evalResult.edge_cases },
              ].map((d) => (
                <span
                  key={d.label}
                  style={{
                    fontSize: 10,
                    fontFamily: "JetBrains Mono, monospace",
                    color: "#9CA3AF",
                    background: "#181C24",
                    border: "1px solid #252A35",
                    borderRadius: 4,
                    padding: "2px 7px",
                  }}
                >
                  {d.label} {d.val}/25
                </span>
              ))}
            </div>
          </div>

          {/* Strengths */}
          {evalResult.strengths && (
            <div
              style={{
                display: "flex",
                gap: 6,
                marginBottom: 6,
                alignItems: "flex-start",
              }}
            >
              <span
                style={{
                  fontSize: 10,
                  color: "#00D4AA",
                  fontFamily: "JetBrains Mono, monospace",
                  flexShrink: 0,
                  paddingTop: 1,
                }}
              >
                STRENGTH
              </span>
              <span style={{ fontSize: 12, color: "#9CA3AF", lineHeight: 1.5 }}>
                {evalResult.strengths}
              </span>
            </div>
          )}

          {/* Improvements */}
          {evalResult.improvements && (
            <div style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
              <span
                style={{
                  fontSize: 10,
                  color: "#FFB800",
                  fontFamily: "JetBrains Mono, monospace",
                  flexShrink: 0,
                  paddingTop: 1,
                }}
              >
                IMPROVE
              </span>
              <span style={{ fontSize: 12, color: "#9CA3AF", lineHeight: 1.5 }}>
                {evalResult.improvements}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function CandidateReport() {
  const { id } = useParams();
  const nav = useNavigate();
  const [downloading, setDownloading] = useState(false);
  const [showGitHubAI, setShowGitHubAI] = useState(false);
  // Live score overrides — updated whenever a skill test is submitted + evaluated
  const [liveScores, setLiveScores] = useState(null);

  const handleScoresUpdated = (scores) => {
    setLiveScores((prev) => ({ ...(prev || {}), ...scores }));
    toast.success("Scores updated ✓", { duration: 2000 });
  };

  // Real data fetched from backend
  const [baseData, setBaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  useEffect(() => {
    if (!id) {
      setFetchError("No candidate ID in URL");
      setLoading(false);
      return;
    }
    fetch(`http://127.0.0.1:8000/candidates/${id}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.success && data.candidate) {
          setBaseData(data.candidate);
        } else {
          setFetchError(data.error || "Candidate not found");
        }
      })
      .catch((err) =>
        setFetchError("Cannot reach backend — is the server running?"),
      )
      .finally(() => setLoading(false));
  }, [id]);

  // Live skill results — initialised from fetched data
  const [skillResults, setSkillResults] = useState(null);

  useEffect(() => {
    if (baseData) {
      setSkillResults((baseData.skill_results || []).map((r) => ({ ...r })));
    }
  }, [baseData]);

  // Called by SkillTestBlock after a successful evaluation
  const handleEvalComplete = (skill, evalData) => {
    setSkillResults((prev) =>
      (prev || []).map((r) => {
        if (r.skill !== skill) return r;
        const verdict = evalData.verdict;
        return {
          ...r,
          passed: verdict === "Pass" || verdict === "Partial",
          score: `${evalData.total}/100`,
        };
      }),
    );
  };

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await generatePDF(c);
      toast.success("PDF downloaded!");
    } catch (e) {
      toast.error("PDF generation failed");
    } finally {
      setDownloading(false);
    }
  };

  // ---- Loading state ----
  if (loading) {
    return (
      <div
        style={{
          padding: "36px 40px",
          display: "flex",
          alignItems: "center",
          gap: 12,
          color: "#6B7280",
        }}
      >
        <Loader2
          size={20}
          color="#6C63FF"
          style={{ animation: "spin 1s linear infinite" }}
        />
        Loading candidate report…
      </div>
    );
  }

  // ---- Error state ----
  if (fetchError || !baseData) {
    return (
      <div style={{ padding: "36px 40px" }}>
        <button
          onClick={() => nav("/")}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "8px 12px",
            background: "#181C24",
            border: "1px solid #252A35",
            borderRadius: 8,
            color: "#6B7280",
            cursor: "pointer",
            fontSize: 13,
            marginBottom: 24,
          }}
        >
          <ArrowLeft size={14} /> Back
        </button>
        <div
          style={{
            background: "rgba(255,107,53,0.08)",
            border: "1px solid rgba(255,107,53,0.3)",
            borderRadius: 14,
            padding: "24px",
          }}
        >
          <AlertTriangle
            size={18}
            color="#FF6B35"
            style={{ marginBottom: 8 }}
          />
          <div style={{ color: "#FF6B35", fontSize: 14 }}>
            {fetchError || "Candidate not found"}
          </div>
        </div>
      </div>
    );
  }

  // Merge live skill results + live scores into candidate data
  const c = {
    ...baseData,
    skill_results: skillResults || baseData.skill_results || [],
    // Live score overrides from backend after skill test submissions
    ...(liveScores || {}),
  };

  const scoreColor =
    c.overall_score >= 80
      ? "#00D4AA"
      : c.overall_score >= 60
        ? "#6C63FF"
        : "#FF6B35";

  return (
    <div style={{ padding: "36px 40px", maxWidth: 1050 }}>
      {/* Header — unchanged */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: 20,
          marginBottom: 32,
        }}
      >
        <button
          onClick={() => nav("/")}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "8px 12px",
            background: "#181C24",
            border: "1px solid #252A35",
            borderRadius: 8,
            color: "#6B7280",
            cursor: "pointer",
            fontSize: 13,
            flexShrink: 0,
          }}
        >
          <ArrowLeft size={14} /> Back
        </button>
        <div style={{ flex: 1 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              marginBottom: 6,
            }}
          >
            <h1
              style={{
                fontFamily: "Syne, sans-serif",
                fontSize: 26,
                fontWeight: 800,
                color: "#E8EAF0",
              }}
            >
              {c.name}
            </h1>
            <StatusBadge
              variant={c.recommendation === "HIRE" ? "hire" : "reject"}
            />
            {c.fraud_flag && (
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 4,
                  fontSize: 10,
                  fontFamily: "JetBrains Mono, monospace",
                  fontWeight: 700,
                  color: "#FFB800",
                  background: "rgba(255,184,0,0.12)",
                  border: "1px solid rgba(255,184,0,0.35)",
                  borderRadius: 6,
                  padding: "3px 8px",
                }}
              >
                ⚠ UNVERIFIED
              </span>
            )}
          </div>
          <div style={{ fontSize: 14, color: "#6B7280" }}>
            {c.role} · {c.location} · {c.email}
          </div>
        </div>
        {/* Action buttons */}
        <div style={{ display: "flex", gap: 10 }}>
          {/* GitHub AI button — only shown when data exists */}
          {c.github_ai && c.github_ai.repos_analysed > 0 && (
            <button
              onClick={() => setShowGitHubAI(true)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "12px 18px",
                background: "rgba(139,92,246,0.12)",
                border: "1px solid rgba(139,92,246,0.4)",
                borderRadius: 10,
                cursor: "pointer",
                fontFamily: "Syne, sans-serif",
                fontWeight: 700,
                fontSize: 13,
                color: "#8B5CF6",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(139,92,246,0.22)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(139,92,246,0.12)";
              }}
            >
              <Github size={15} />
              GitHub AI{" "}
              <span
                style={{
                  fontFamily: "JetBrains Mono, monospace",
                  fontSize: 11,
                  color:
                    c.github_ai.overall_ai_probability >= 0.6
                      ? "#FF6B35"
                      : c.github_ai.overall_ai_probability >= 0.35
                        ? "#FFB800"
                        : "#00D4AA",
                }}
              >
                {Math.round(c.github_ai.overall_ai_probability * 100)}%
              </span>
            </button>
          )}

          <button
            onClick={handleDownload}
            disabled={downloading}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "12px 20px",
              background: downloading
                ? "#252A35"
                : "linear-gradient(135deg, #6C63FF, #00D4AA)",
              border: "none",
              borderRadius: 10,
              cursor: downloading ? "not-allowed" : "pointer",
              fontFamily: "Syne, sans-serif",
              fontWeight: 700,
              fontSize: 13,
              color: "#fff",
            }}
          >
            <Download size={15} />
            {downloading ? "Generating…" : "Download PDF"}
          </button>
        </div>
      </div>

      {/* Score overview — unchanged */}
      <Card
        style={{
          marginBottom: 24,
          display: "flex",
          alignItems: "center",
          gap: 32,
        }}
      >
        <ScoreRing
          score={c.overall_score}
          size={100}
          strokeWidth={8}
          color="auto"
          label="Overall"
        />
        <div
          style={{
            flex: 1,
            display: "grid",
            gridTemplateColumns: "repeat(3,1fr)",
            gap: 20,
          }}
        >
          {[
            {
              label: "Profile Score",
              score: c.profile_score,
              color: "#00D4AA",
            },
            { label: "SAS Score", score: c.sas_score, color: "#6C63FF" },
            { label: "Skill Score", score: c.skill_score, color: "#FFB800" },
          ].map((s) => (
            <div key={s.label}>
              <div
                style={{
                  fontSize: 11,
                  color: "#6B7280",
                  fontFamily: "JetBrains Mono, monospace",
                  marginBottom: 6,
                  letterSpacing: "0.06em",
                }}
              >
                {s.label.toUpperCase()}
              </div>
              <div
                style={{
                  fontFamily: "Syne, sans-serif",
                  fontSize: 36,
                  fontWeight: 800,
                  color: s.color,
                  lineHeight: 1,
                }}
              >
                {s.score}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* 2-col layout — unchanged */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 20,
          marginBottom: 24,
        }}
      >
        {/* SAS Breakdown */}
        <Card>
          <Section title="SAS SCORE BREAKDOWN">
            {/* Weight legend */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 14,
              }}
            >
              <span
                style={{
                  fontSize: 10,
                  color: "#4B5563",
                  fontFamily: "JetBrains Mono, monospace",
                }}
              >
                COMPONENT (weighted contribution)
              </span>
              <span
                style={{
                  fontSize: 10,
                  color: "#4B5563",
                  fontFamily: "JetBrains Mono, monospace",
                }}
              >
                / MAX
              </span>
            </div>

            {/* The 4 bars with their max weights */}
            {[
              {
                key: "profile_completeness",
                label: "Profile Completeness",
                max: 40,
                weight: "40%",
              },
              {
                key: "evidence_score",
                label: "Evidence Score",
                max: 30,
                weight: "30%",
              },
              {
                key: "skill_coverage",
                label: "Skill Coverage",
                max: 20,
                weight: "20%",
              },
              {
                key: "fraud_risk_inverse",
                label: "Trust Signal",
                max: 10,
                weight: "10%",
              },
            ].map((item, i) => {
              const val = (c.sas_breakdown || {})[item.key] ?? 0;
              return (
                <div key={item.key} style={{ marginBottom: 12 }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: 5,
                    }}
                  >
                    <div
                      style={{ display: "flex", alignItems: "center", gap: 8 }}
                    >
                      <span style={{ fontSize: 12, color: "#E8EAF0" }}>
                        {item.label}
                      </span>
                      <span
                        style={{
                          fontSize: 9,
                          fontFamily: "JetBrains Mono, monospace",
                          color: "#6B7280",
                          background: "#252A35",
                          borderRadius: 3,
                          padding: "1px 5px",
                        }}
                      >
                        {item.weight}
                      </span>
                    </div>
                    <span
                      style={{
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: 12,
                        color: "#E8EAF0",
                        fontWeight: 700,
                      }}
                    >
                      {val}
                      <span style={{ color: "#4B5563", fontWeight: 400 }}>
                        /{item.max}
                      </span>
                    </span>
                  </div>
                  <div
                    style={{
                      height: 6,
                      background: "#252A35",
                      borderRadius: 999,
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${Math.min((val / item.max) * 100, 100)}%`,
                        background: "linear-gradient(90deg, #6C63FF, #00D4AA)",
                        borderRadius: 999,
                        transition: `width 0.6s ease ${i * 0.1}s`,
                      }}
                    />
                  </div>
                </div>
              );
            })}

            {/* Sum footer */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: 16,
                paddingTop: 12,
                borderTop: "1px solid #252A35",
              }}
            >
              <span
                style={{
                  fontSize: 11,
                  color: "#6B7280",
                  fontFamily: "JetBrains Mono, monospace",
                }}
              >
                SAS TOTAL
              </span>
              <span
                style={{
                  fontSize: 18,
                  fontWeight: 800,
                  fontFamily: "Syne, sans-serif",
                  color: "#6C63FF",
                }}
              >
                {Object.values(c.sas_breakdown || {}).reduce(
                  (a, b) => a + b,
                  0,
                )}
                <span
                  style={{
                    fontSize: 12,
                    color: "#4B5563",
                    fontFamily: "JetBrains Mono, monospace",
                    fontWeight: 400,
                  }}
                >
                  /100
                </span>
              </span>
            </div>
          </Section>

          {c.fraud_flag && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginTop: 8,
                padding: "10px 14px",
                background: "rgba(255,184,0,0.08)",
                borderRadius: 8,
                border: "1px solid rgba(255,184,0,0.3)",
              }}
            >
              <AlertTriangle size={14} color="#FFB800" />
              <span style={{ fontSize: 12, color: "#FFB800" }}>
                Unverified skills detected — manual review recommended
              </span>
            </div>
          )}
        </Card>

        {/* Skill test results — layout unchanged, SkillTestBlock added inline */}
        <Card>
          <Section title="SKILL TESTING RESULTS">
            {c.skill_results.map((r) => {
              const question = c.skill_questions?.[r.skill] || "";
              const evidenceScore =
                c.evidence?.aggregated_skill_scores?.[r.skill] ?? 0.0;

              return (
                <div key={r.skill}>
                  {/* Original row — visual unchanged */}
                  <SkillTestRow result={r} />

                  {/*
                    If a question exists for this skill (weak/missing evidence),
                    render the interactive test block.
                    If the skill is already evaluated (score !== "Pending"),
                    SkillTestBlock will still show the question read-only since
                    evalResult drives its internal state.
                    Skills without a question (strong evidence, score "Verified")
                    render nothing extra — same as before.
                  */}
                  {question && (
                    <SkillTestBlock
                      skill={r.skill}
                      question={question}
                      evidenceScore={evidenceScore}
                      candidateId={c.id}
                      onEvalComplete={handleEvalComplete}
                      onScoresUpdated={handleScoresUpdated}
                    />
                  )}
                </div>
              );
            })}
          </Section>

          {/* Matched skills chips — unchanged */}
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            {(c.skills_matched || []).map((s) => (
              <span
                key={s}
                style={{
                  fontSize: 11,
                  padding: "3px 10px",
                  borderRadius: 20,
                  background: "rgba(0,212,170,0.1)",
                  border: "1px solid rgba(0,212,170,0.3)",
                  color: "#00D4AA",
                  fontFamily: "JetBrains Mono, monospace",
                }}
              >
                {s}
              </span>
            ))}
          </div>
        </Card>
      </div>

      {/* Resume Engine — only shown when improvements exist */}
      {(c.resume_improvements || []).length > 0 && (
        <Card>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 16,
            }}
          >
            <div
              style={{
                fontSize: 10,
                color: "#6B7280",
                fontFamily: "JetBrains Mono, monospace",
                letterSpacing: "0.1em",
              }}
            >
              RESUME ENGINE — IMPROVEMENTS
            </div>
            <div
              style={{
                display: "flex",
                gap: 16,
                fontSize: 11,
                fontFamily: "JetBrains Mono, monospace",
              }}
            >
              <span style={{ color: "#FF6B35" }}>■ BEFORE</span>
              <span style={{ color: "#00D4AA" }}>■ AFTER</span>
            </div>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "100px 1fr 1fr",
              gap: 16,
              paddingBottom: 10,
              borderBottom: "1px solid #252A35",
            }}
          >
            {["SECTION", "ORIGINAL ISSUE", "AI-IMPROVED VERSION"].map((h) => (
              <div
                key={h}
                style={{
                  fontSize: 10,
                  color: "#6B7280",
                  fontFamily: "JetBrains Mono, monospace",
                  letterSpacing: "0.06em",
                }}
              >
                {h}
              </div>
            ))}
          </div>
          {(c.resume_improvements || []).map((item, i) => (
            <ImprovementRow key={item.section} item={item} index={i} />
          ))}
        </Card>
      )}

      {/* GitHub AI deep-dive modal */}
      {showGitHubAI && (
        <GitHubAIModal
          data={c.github_ai}
          onClose={() => setShowGitHubAI(false)}
        />
      )}
    </div>
  );
}
