import { apiPost, apiPut, apiGet, setAuthTokens } from './client.js'

export async function verifyPassword(password) {
  const result = await apiPost('/admin/verify', { password })
  if (result.ok && result.data) setAuthTokens(result.data)
  return result
}

export function changePassword(oldPassword, newPassword) {
  return apiPut('/admin/password', { old_password: oldPassword, new_password: newPassword })
}

export function fetchSettings() {
  return apiGet('/admin/settings')
}

export function updateSettings(data) {
  return apiPut('/admin/settings', data)
}

export function testEmail(email) {
  return apiPost('/admin/test-email', { email })
}
