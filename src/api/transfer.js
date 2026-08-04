import { apiPost } from './client.js'

export function transfer(data) {
  return apiPost('/transfer', data)
}
