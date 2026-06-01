/**
 * pdfGenerator.js
 * Generates the candidate evaluation PDF using jsPDF.
 * This is the "Resume Engine" output — Person 5's deliverable.
 *
 * ReportLab (Python) on the backend generates the server-side PDF.
 * This client-side version is for instant demo downloads.
 */
import jsPDF from 'jspdf'

const COLORS = {
  bg:      [10,  12,  16],
  surface: [24,  28,  36],
  accent:  [108, 99,  255],
  green:   [0,   212, 170],
  orange:  [255, 107, 53],
  text:    [232, 234, 240],
  muted:   [107, 114, 128],
  border:  [37,  42,  53],
}

function hex(rgb) {
  return rgb
}

export async function generatePDF(candidate) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const W = 210
  const MARGIN = 16
  let y = 0

  // ── Helper functions ────────────────────────────────────────────────────────
  const fill = (r, g, b) => doc.setFillColor(r, g, b)
  const stroke = (r, g, b) => doc.setDrawColor(r, g, b)
  const textColor = (r, g, b) => doc.setTextColor(r, g, b)
  const rect = (x, _y, w, h, style = 'F') => doc.rect(x, _y, w, h, style)
  const line = (x1, y1, x2, y2) => doc.line(x1, y1, x2, y2)

  // ── Cover header ────────────────────────────────────────────────────────────
  fill(...COLORS.bg)
  rect(0, 0, W, 297)

  // Accent bar
  fill(...COLORS.accent)
  rect(0, 0, W, 40)

  textColor(255, 255, 255)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(22)
  doc.text('TalentLens', MARGIN, 17)

  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  doc.text('AI Candidate Evaluation Report', MARGIN, 24)
  doc.text(`Generated: ${new Date().toLocaleDateString('en-GB')}`, MARGIN, 30)

  // Recommendation badge (top-right)
  const rec = candidate.recommendation || 'HIRE'
  const recColor = rec === 'HIRE' ? COLORS.green : COLORS.orange
  fill(...recColor)
  doc.roundedRect(W - MARGIN - 30, 14, 30, 12, 2, 2, 'F')
  textColor(10, 12, 16)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(10)
  doc.text(rec, W - MARGIN - 15, 22, { align: 'center' })

  y = 52

  // ── Candidate info ──────────────────────────────────────────────────────────
  fill(...COLORS.surface)
  doc.roundedRect(MARGIN, y, W - MARGIN * 2, 36, 3, 3, 'F')

  textColor(...COLORS.text)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(16)
  doc.text(candidate.name, MARGIN + 6, y + 11)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  textColor(...COLORS.muted)
  doc.text(candidate.role || '', MARGIN + 6, y + 18)
  doc.text(candidate.email || '', MARGIN + 6, y + 25)
  doc.text(candidate.location || '', MARGIN + 6, y + 31)

  y += 44

  // ── Score overview ──────────────────────────────────────────────────────────
  const scores = [
    { label: 'Overall',  value: candidate.overall_score, color: COLORS.accent },
    { label: 'Profile',  value: candidate.profile_score, color: COLORS.green },
    { label: 'SAS',      value: candidate.sas_score,     color: COLORS.accent },
    { label: 'Skills',   value: candidate.skill_score,   color: [255, 184, 0] },
  ]

  const boxW = (W - MARGIN * 2 - 12) / 4
  scores.forEach((s, i) => {
    const bx = MARGIN + i * (boxW + 4)
    fill(...COLORS.surface)
    doc.roundedRect(bx, y, boxW, 26, 2, 2, 'F')

    // Score value
    textColor(...s.color)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(20)
    doc.text(String(s.value || 0), bx + boxW / 2, y + 14, { align: 'center' })

    // Label
    textColor(...COLORS.muted)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7)
    doc.text(s.label.toUpperCase(), bx + boxW / 2, y + 21, { align: 'center' })
  })

  y += 34

  // ── SAS Breakdown ───────────────────────────────────────────────────────────
  if (candidate.sas_breakdown) {
    textColor(...COLORS.muted)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(8)
    doc.text('SAS SCORE BREAKDOWN', MARGIN, y)
    y += 6

    Object.entries(candidate.sas_breakdown).forEach(([key, val]) => {
      const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      const barW = W - MARGIN * 2 - 30
      const fillW = (val / 100) * barW

      textColor(...COLORS.text)
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9)
      doc.text(label, MARGIN, y + 3)

      // Bar track
      fill(...COLORS.border)
      doc.roundedRect(MARGIN + 46, y - 1, barW, 5, 1, 1, 'F')

      // Bar fill
      const barColor = val >= 80 ? COLORS.green : val >= 60 ? COLORS.accent : COLORS.orange
      fill(...barColor)
      if (fillW > 0) doc.roundedRect(MARGIN + 46, y - 1, fillW, 5, 1, 1, 'F')

      textColor(...COLORS.muted)
      doc.setFontSize(8)
      doc.text(String(val), MARGIN + 46 + barW + 4, y + 3)

      y += 9
    })

    y += 4
  }

  // ── Skill Test Results ──────────────────────────────────────────────────────
  if (candidate.skill_results?.length) {
    textColor(...COLORS.muted)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(8)
    doc.text('SKILL TESTING RESULTS', MARGIN, y)
    y += 6

    candidate.skill_results.forEach(r => {
      const color = r.passed ? COLORS.green : COLORS.orange
      const icon = r.passed ? '✓' : '✗'

      textColor(...color)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(9)
      doc.text(icon, MARGIN, y + 3)

      textColor(...COLORS.text)
      doc.setFont('helvetica', 'normal')
      doc.text(r.skill, MARGIN + 5, y + 3)

      textColor(...COLORS.muted)
      doc.setFontSize(8)
      doc.text(`${r.difficulty}`, MARGIN + 35, y + 3)

      textColor(...color)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(9)
      doc.text(String(r.score), MARGIN + 60, y + 3)

      y += 8
    })

    y += 4
  }

  // ── Resume Improvements ─────────────────────────────────────────────────────
  if (candidate.resume_improvements?.length) {
    // New page if needed
    if (y > 230) { doc.addPage(); fill(...COLORS.bg); rect(0, 0, W, 297); y = 20 }

    textColor(...COLORS.muted)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(8)
    doc.text('RESUME ENGINE — BEFORE / AFTER IMPROVEMENTS', MARGIN, y)
    y += 8

    candidate.resume_improvements.forEach((item, i) => {
      if (y > 260) { doc.addPage(); fill(...COLORS.bg); rect(0, 0, W, 297); y = 20 }

      fill(...COLORS.surface)
      doc.roundedRect(MARGIN, y, W - MARGIN * 2, 28, 2, 2, 'F')

      // Section badge
      fill(...COLORS.accent)
      doc.roundedRect(MARGIN + 4, y + 4, 22, 8, 1, 1, 'F')
      textColor(255, 255, 255)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(6)
      doc.text(item.section.toUpperCase(), MARGIN + 15, y + 9.5, { align: 'center' })

      // Before
      textColor(...COLORS.orange)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(7)
      doc.text('BEFORE', MARGIN + 30, y + 7)
      textColor(...COLORS.muted)
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(8)
      const beforeLines = doc.splitTextToSize(item.issue, 68)
      doc.text(beforeLines, MARGIN + 30, y + 13)

      // After
      const halfW = (W - MARGIN * 2) / 2
      textColor(...COLORS.green)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(7)
      doc.text('AFTER', MARGIN + halfW + 2, y + 7)
      textColor(...COLORS.text)
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(8)
      const afterLines = doc.splitTextToSize(item.fix, 68)
      doc.text(afterLines, MARGIN + halfW + 2, y + 13)

      y += 32
    })
  }

  // ── Footer ──────────────────────────────────────────────────────────────────
  if (y > 260) { doc.addPage(); fill(...COLORS.bg); rect(0, 0, W, 297); y = 250 }

  fill(...COLORS.accent)
  rect(0, 287, W, 10)
  textColor(255, 255, 255)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7)
  doc.text('TalentLens — AI Candidate Evaluation · Generated by Person 5 · Resume Engine', W / 2, 293, { align: 'center' })

  // ── Save ────────────────────────────────────────────────────────────────────
  doc.save(`TalentLens_${candidate.name.replace(/\s+/g, '_')}_Report.pdf`)
}
