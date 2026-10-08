import axios from 'axios'

const BASE = '/api'

const api = axios.create({ baseURL: BASE })

// ── Calls ──────────────────────────────────────────────────────────────────
export const getCalls = (page = 1) =>
  api.get(`/calls?page=${page}&per_page=20`).then(r => r.data)

export const getCall = (id) =>
  api.get(`/calls/${id}`).then(r => r.data)

// ── Stats ──────────────────────────────────────────────────────────────────
export const getStats = () =>
  api.get('/stats').then(r => r.data)

// ── Upload ─────────────────────────────────────────────────────────────────
export const uploadCall = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/calls/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => {
      if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
    },
  }).then(r => r.data)
}

// ── Actions ────────────────────────────────────────────────────────────────
export const updateAction = (id, status, assigned_to) =>
  api.patch(`/actions/${id}`, { status, assigned_to }).then(r => r.data)
