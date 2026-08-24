import { apiGet, apiPut } from './client.js'

export function fetchUsers(params = {}) {
  return apiGet('/users', params)
}

export function updateUser(id, data) {
  return apiPut(`/users/${id}`, data)
}

