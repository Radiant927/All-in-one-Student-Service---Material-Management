const BASE = '/api'

async function request(path, options = {}) {
  const url = `${BASE}${path}`
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  }
  try {
    const res = await fetch(url, config)
    const data = await res.json()
    return data
  } catch (e) {
    return { ok: false, data: null, msg: `网络错误: ${e.message}` }
  }
}

export function apiGet(path, params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.append(k, v)
  })
  const query = qs.toString()
  return request(`${path}${query ? '?' + query : ''}`)
}

export function apiPost(path, body = {}) {
  return request(path, { method: 'POST', body: JSON.stringify(body) })
}

export function apiPut(path, body = {}) {
  return request(path, { method: 'PUT', body: JSON.stringify(body) })
}

export function apiDelete(path) {
  return request(path, { method: 'DELETE' })
}

export async function apiUpload(path, file) {
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await fetch(`${BASE}${path}`, { method: 'POST', body: formData })
    return await res.json()
  } catch (e) {
    return { ok: false, data: null, msg: `网络错误: ${e.message}` }
  }
}