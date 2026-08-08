const BASE = '/api'
const ACCESS_TOKEN_KEY = 'material_access_token'
const REFRESH_TOKEN_KEY = 'material_refresh_token'

export function setAuthTokens(data) {
  if (data?.access_token) localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
  if (data?.refresh_token) localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
}

export function clearAuthTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

async function request(path, options = {}) {
  const url = `${BASE}${path}`
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  }
  try {
    const res = await fetch(url, config)
    const data = await res.json()
    if (res.status === 401 && !options._retried && path !== '/auth/refresh') {
      const refreshed = await refreshAccessToken()
      if (refreshed) return request(path, { ...options, _retried: true })
    }
    return data
  } catch (e) {
    return { ok: false, data: null, msg: `网络错误: ${e.message}` }
  }
}

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refreshToken) return false
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    const data = await res.json()
    if (!res.ok || !data.ok) {
      clearAuthTokens()
      return false
    }
    setAuthTokens(data.data)
    return true
  } catch {
    return false
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
    const token = localStorage.getItem(ACCESS_TOKEN_KEY)
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })
    return await res.json()
  } catch (e) {
    return { ok: false, data: null, msg: `网络错误: ${e.message}` }
  }
}
