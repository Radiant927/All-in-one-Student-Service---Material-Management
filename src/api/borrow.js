import { apiGet, apiPost } from './client.js'

export function borrow(data) {
  return apiPost('/borrow', data)
}

export function returnItem(data) {
  return apiPost('/return', data)
}

export function fetchHistory(params = {}) {
  return apiGet('/history', params)
}