import { apiGet, apiPost, apiPut, apiDelete } from './client.js'

export function fetchMaterials(params = {}) {
  return apiGet('/materials', params)
}

export function fetchMaterial(id) {
  return apiGet(`/materials/${id}`)
}

export function createMaterial(data) {
  return apiPost('/materials', data)
}

export function updateMaterial(id, data) {
  return apiPut(`/materials/${id}`, data)
}

export function deleteMaterial(id) {
  return apiDelete(`/materials/${id}`)
}