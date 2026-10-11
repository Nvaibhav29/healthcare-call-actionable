import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import UploadModal from '../components/UploadModal'
import { getCalls } from '../services/api'

function sentimentClass(s) {
  if (s === 'frustrated') return 'sentiment-frustrated'
  if (s === 'satisfied') return 'sentiment-satisfied'
  return 'sentiment-neutral'
}

function statusTag(s) {
  if (s === 'processing') return 'tag tag-blue'
  if (s === 'routed') return 'tag tag-green'
  if (s === 'needs_review') return 'tag tag-amber'
  return 'tag tag-gray'
}

function fmtDate(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function fmtTime(iso) {
  return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })
}

function fmtId(id) {
  return '#' + id.slice(0, 6).toUpperCase()
}

export default function AllCalls() {
  const navigate = useNavigate()
  const [calls, setCalls] = useState([])
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showUpload, setShowUpload] = useState(false)

  const load = async (p) => {
    try {
      setLoading(true)
      const data = await getCalls(p)
      setCalls(data.calls || [])
    } catch (e) {
      setError('Could not reach backend. Make sure the server is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(page) }, [page])

  const handleDone = result => {
    setShowUpload(false)
    navigate(`/calls/${result.call_id}`)
  }

  return (
    <div className="app-shell">
      <Sidebar />

      <div className="main-area">
        {/* Topbar */}
        <div className="topbar">
          <div className="topbar-breadcrumb">
            <strong>All Calls</strong>
          </div>
          <div className="topbar-status">
            <div className="dot-green" />
            Live
          </div>
          <button className="btn btn-primary btn-sm" onClick={() => setShowUpload(true)}>
            Process New Call
          </button>
        </div>

        {/* Content */}
        <div className="page-content">
          {error && (
            <div className="review-banner" style={{ marginBottom: 20 }}>{error}</div>
          )}

          <div className="section-header">
            <span className="section-title">Processed Calls</span>
            <span className="section-sub">{calls.length} on this page</span>
          </div>

          <div className="card">
            {loading
              ? <div style={{ padding: 24, textAlign: 'center' }}><div className="spinner" style={{ margin: '0 auto' }} /></div>
              : calls.length === 0
                ? <div style={{ padding: 24, textAlign: 'center', color: 'var(--c-text-muted)', fontSize: 13 }}>
                    No calls processed yet. Upload one to get started.
                  </div>
                : <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Time</th>
                        <th>Call ID</th>
                        <th>Name</th>
                        <th>Patient ID</th>
                        <th>Sentiment</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {calls.map(c => (
                        <tr key={c.id} className="clickable"
                          onClick={() => navigate(`/calls/${c.id}`)}>
                          <td className="text-sm">{fmtDate(c.created_at)}</td>
                          <td className="mono text-sm">{fmtTime(c.created_at)}</td>
                          <td className="mono text-sm">{fmtId(c.id)}</td>
                          <td>{c.patient_name || '—'}</td>
                          <td className="mono text-sm">{c.patient_id || '—'}</td>
                          <td>
                            <span className={sentimentClass(c.sentiment)}>
                              {c.sentiment ? c.sentiment.charAt(0).toUpperCase() + c.sentiment.slice(1) : '—'}
                            </span>
                          </td>
                          <td>
                            <span className={statusTag(c.status)}>
                              {c.status === 'needs_review' ? 'Needs Review' :
                                c.status ? c.status.charAt(0).toUpperCase() + c.status.slice(1) : '—'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
            }
          </div>

          {/* Pagination */}
          {!loading && calls.length > 0 && (
            <div className="pagination-row">
              <button
                className="btn btn-sm"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >
                Previous
              </button>
              <span className="pagination-label">Page {page}</span>
              <button
                className="btn btn-sm"
                disabled={calls.length < 20}
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>

      {showUpload && <UploadModal onClose={() => setShowUpload(false)} onDone={handleDone} />}
    </div>
  )
}
