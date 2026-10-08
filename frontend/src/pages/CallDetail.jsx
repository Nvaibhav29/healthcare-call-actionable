import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import ActionCard from '../components/ActionCard'
import { getCall } from '../services/api'

function sentimentTag(s) {
  const map = { frustrated: 'tag tag-red', neutral: 'tag tag-gray', satisfied: 'tag tag-green' }
  return map[s] || 'tag tag-gray'
}

function fmtDuration(s) {
  if (!s) return '—'
  const m = Math.floor(s / 60), sec = s % 60
  return `${m}:${String(sec).padStart(2, '0')}`
}

function fmtDatetime(iso) {
  return new Date(iso).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false,
  })
}

function fmtId(id) {
  return '#' + id.slice(0, 6).toUpperCase()
}

// Highlight trigger phrases in transcript line
function HighlightText({ text, triggers = [] }) {
  if (!triggers.length) return <>{text}</>
  const pattern = triggers.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')
  const regex = new RegExp(`(${pattern})`, 'gi')
  const parts = text.split(regex)
  return (
    <>
      {parts.map((p, i) =>
        regex.test(p) ? <u key={i}>{p}</u> : <span key={i}>{p}</span>
      )}
    </>
  )
}

export default function CallDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getCall(id)
      .then(setData)
      .catch(() => setError('Call not found or backend unavailable.'))
      .finally(() => setLoading(false))
  }, [id])

  const call = data?.call
  const actions = data?.actions || []
  const triggers = actions.map(a => a.trigger_phrase).filter(Boolean)

  // Parse transcript lines — try to split by [PATIENT]/[STAFF] markers
  const parseTranscript = (raw = '') => {
    if (!raw) return []
    const regex = /\[(PATIENT|STAFF)\]/gi
    if (!regex.test(raw)) {
      // No speaker tags — show as plain lines
      return raw.split('\n').filter(l => l.trim()).map((l, i) => ({
        lineNum: i + 1, speaker: null, text: l.trim(),
      }))
    }
    // Split by speaker markers
    const parts = raw.split(/(\[(?:PATIENT|STAFF)\])/gi).filter(Boolean)
    const lines = []
    let idx = 0, lineNum = 1
    while (idx < parts.length) {
      const tag = parts[idx]?.match(/\[(PATIENT|STAFF)\]/i)
      if (tag) {
        const speaker = tag[1].toUpperCase()
        const text = (parts[idx + 1] || '').trim()
        if (text) lines.push({ lineNum: lineNum++, speaker, text })
        idx += 2
      } else { idx++ }
    }
    return lines.length ? lines : [{ lineNum: 1, speaker: null, text: raw }]
  }

  const transcriptLines = parseTranscript(call?.raw_transcript)

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-area">
        {/* Topbar */}
        <div className="topbar">
          <div className="topbar-breadcrumb">
            <span
              style={{ cursor: 'pointer', color: 'var(--c-primary)' }}
              onClick={() => navigate('/dashboard')}
            >Dashboard</span>
            <span> / </span>
            <strong>{call ? fmtId(call.id) : '…'}</strong>
          </div>
          {call && (
            <div style={{ display: 'flex', gap: 12, alignItems: 'center',
              fontSize: 12, color: 'var(--c-text-muted)' }}>
              <span>Duration {fmtDuration(call.duration_seconds)}</span>
              <span>ASR: {call.asr_provider}</span>
              <span>LLM: {call.llm_provider}</span>
            </div>
          )}
        </div>

        <div className="page-content">
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
              <div className="spinner" />
            </div>
          )}
          {error && <div className="review-banner">{error}</div>}

          {call && (
            <>
              {/* Call header card */}
              <div className="card card-body" style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                  <span className="mono" style={{ fontSize: 22, fontWeight: 700 }}>
                    {fmtId(call.id)}
                  </span>
                  <span style={{ fontSize: 13, color: 'var(--c-text-muted)' }}>
                    {fmtDatetime(call.created_at)}
                  </span>
                  {call.language_detected && (
                    <span className="tag tag-outline">{call.language_detected}</span>
                  )}
                  <span className={sentimentTag(call.sentiment)}
                    style={{ textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700, fontSize: 11 }}>
                    {call.sentiment || 'unknown'}
                  </span>
                  {call.needs_review && (
                    <span className="tag tag-amber">Needs Review</span>
                  )}
                </div>

                {/* Confidence + speaker bars */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: 14 }}>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--c-text-muted)', marginBottom: 5, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      Extraction Confidence
                    </div>
                    <div className="conf-row">
                      <div className="conf-track">
                        <div className="conf-fill"
                          style={{ width: `${Math.round((call.confidence_score || 0.8) * 100)}%` }} />
                      </div>
                      <span className="conf-label">
                        {Math.round((call.confidence_score || 0.8) * 100)}%
                      </span>
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--c-text-muted)', marginBottom: 5, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      {actions.length} Action{actions.length !== 1 ? 's' : ''} Extracted
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {['high', 'medium', 'low'].map(p => {
                        const count = actions.filter(a => a.priority === p).length
                        return count ? (
                          <span key={p} className={`tag tag-${p === 'high' ? 'red' : p === 'medium' ? 'amber' : 'gray'}`}>
                            {count} {p}
                          </span>
                        ) : null
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {call.needs_review && (
                <div className="review-banner">
                  One or more actions have low confidence. Review and verify before acting.
                </div>
              )}

              {/* Two-col */}
              <div className="two-col">
                {/* Left: Summary + Actions */}
                <div>
                  {/* AI Summary */}
                  <div className="section-header">
                    <span className="section-title">AI Summary</span>
                  </div>
                  <div className="card card-body" style={{ marginBottom: 20 }}>
                    <p style={{ fontSize: 13, color: 'var(--c-text-primary)', lineHeight: 1.7 }}>
                      {call.ai_summary || 'No summary generated.'}
                    </p>
                  </div>

                  {/* Extracted Actions */}
                  <div className="section-header">
                    <span className="section-title">Extracted Actions</span>
                    <span className="section-sub">{actions.length} items</span>
                  </div>
                  {actions.length === 0
                    ? <div className="card card-body">
                        <p style={{ color: 'var(--c-text-muted)', fontSize: 13 }}>
                          No actions extracted.
                        </p>
                      </div>
                    : actions.map(a => <ActionCard key={a.id} action={a} />)
                  }
                </div>

                {/* Right: Transcript */}
                <div>
                  <div className="section-header">
                    <span className="section-title">Full Transcript</span>
                    {call.language_detected && (
                      <span className="tag tag-outline" style={{ fontSize: 10 }}>
                        {call.language_detected}
                      </span>
                    )}
                  </div>
                  <div className="card">
                    <div className="transcript-block">
                      {transcriptLines.length === 0
                        ? <p style={{ color: 'var(--c-text-muted)', fontSize: 13 }}>No transcript.</p>
                        : transcriptLines.map(l => (
                            <div key={l.lineNum} className="transcript-line">
                              <span className="t-line-num">{String(l.lineNum).padStart(2, '0')}</span>
                              <span className={`t-speaker ${l.speaker === 'PATIENT' ? 'patient' : 'staff'}`}>
                                {l.speaker ? `[${l.speaker}]` : ''}
                              </span>
                              <span className="t-text">
                                <HighlightText text={l.text} triggers={triggers} />
                              </span>
                            </div>
                          ))
                      }
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
