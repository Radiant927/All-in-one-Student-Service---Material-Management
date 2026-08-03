import { apiPost, apiPut } from './client.js'

export function verifyPassword(password) {
  return apiPost('/admin/verify', { password })
}

export function changePassword(oldPassword, newPassword) {
  return apiPut('/admin/password', { old_password: oldPassword, new_password: newPassword })
}