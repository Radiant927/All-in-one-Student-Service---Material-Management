const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'
const ACCESS_KEY = 'material_access_token'
const REFRESH_KEY = 'material_refresh_token'

export function saveTokens(data) {
  uni.setStorageSync(ACCESS_KEY, data.access_token)
  uni.setStorageSync(REFRESH_KEY, data.refresh_token)
  if (data.user) uni.setStorageSync('material_user', data.user)
}

export function clearTokens() {
  uni.removeStorageSync(ACCESS_KEY)
  uni.removeStorageSync(REFRESH_KEY)
  uni.removeStorageSync('material_user')
}

function rawRequest(path, method, data, token) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${path}`,
      method,
      data,
      timeout: 12000,
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success: resolve,
      fail: reject,
    })
  })
}

async function refreshToken() {
  const refresh = uni.getStorageSync(REFRESH_KEY)
  if (!refresh) return false
  try {
    const response = await rawRequest('/auth/refresh', 'POST', { refresh_token: refresh })
    if (!response.data?.ok) return false
    saveTokens(response.data.data)
    return true
  } catch {
    return false
  }
}

export async function request(path, options = {}) {
  const method = options.method || 'GET'
  try {
    let response = await rawRequest(path, method, options.data, uni.getStorageSync(ACCESS_KEY))
    if (response.statusCode === 401 && !options.retried && await refreshToken()) {
      response = await rawRequest(path, method, options.data, uni.getStorageSync(ACCESS_KEY))
    }
    if (!response.data?.ok) throw new Error(response.data?.msg || '请求失败')
    return response.data.data
  } catch (error) {
    uni.showToast({ title: error.message || '网络异常', icon: 'none' })
    throw error
  }
}

export function requireLogin() {
  if (!uni.getStorageSync(ACCESS_KEY)) {
    uni.reLaunch({ url: '/pages/login/index' })
    return false
  }
  return true
}

