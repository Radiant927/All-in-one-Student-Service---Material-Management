import { apiPost, apiPut, apiGet } from './client.js'

export function verifyPassword(password) {
  return apiPost('/admin/verify', { password })
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