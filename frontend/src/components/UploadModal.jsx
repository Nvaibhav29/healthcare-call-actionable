import { useState, useRef } from 'react'
import { uploadCall } from '../services/api'

export default function UploadModal({ onClose, onDone }) {
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState(null)
  const [progress, setProgress] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef()

  const handleFile = f => {
    setError('')
    setFile(f)
  }

  const handleDrop = e => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const result = await uploadCall(file, setProgress)
      onDone(result)
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed. Check backend.')
      setLoading(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: '#fff', border: '1px solid var(--c-border)',
        borderRadius: 'var(--radius)', width: 480, padding: 24,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontFamily: 'var(--font-head)', fontSize: 15, fontWeight: 700 }}>
            Process New Call
          </h2>
          <button
            onClick={onClose}
            style={{ marginLeft: 'auto', background: 'none', border: 'none',
              cursor: 'pointer', color: 'var(--c-text-muted)', fontSize: 18 }}
          >
            ×
          </button>
        </div>

        <div
          className={`upload-zone ${dragging ? 'dragging' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current.click()}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
            stroke="var(--c-text-muted)" strokeWidth="1.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          {file
            ? <p><strong>{file.name}</strong> ({(file.size / 1024 / 1024).toFixed(2)} MB)</p>
            : <p>Drop audio file here or <strong>click to browse</strong></p>
          }
          <p className="text-sm" style={{ marginTop: 4 }}>
            Supports WAV, MP3, M4A, OGG, FLAC — max 50 MB
          </p>
          <input ref={inputRef} type="file"
            accept=".wav,.mp3,.m4a,.ogg,.flac,.webm"
            style={{ display: 'none' }}
            onChange={e => handleFile(e.target.files[0])} />
        </div>

        {loading && (
          <div style={{ marginTop: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between',
              fontSize: 12, color: 'var(--c-text-muted)', marginBottom: 4 }}>
              <span>Processing…</span>
              <span>{progress}%</span>
            </div>
            <div className="dept-bar-track">
              <div className="dept-bar-fill bar-blue" style={{ width: `${progress}%` }} />
            </div>
            <p style={{ fontSize: 12, color: 'var(--c-text-muted)', marginTop: 8 }}>
              ASR + LLM extraction running. This takes 15–60 seconds.
            </p>
          </div>
        )}

        {error && (
          <p style={{ marginTop: 12, fontSize: 12, color: 'var(--c-danger)' }}>{error}</p>
        )}

        <div style={{ display: 'flex', gap: 8, marginTop: 20, justifyContent: 'flex-end' }}>
          <button className="btn btn-outline" onClick={onClose} disabled={loading}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit}
            disabled={!file || loading}>
            {loading ? <><div className="spinner" /> Processing</> : 'Process Call'}
          </button>
        </div>
      </div>
    </div>
  )
}
