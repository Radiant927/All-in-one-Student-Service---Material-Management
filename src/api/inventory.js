import { apiGet, apiPost, apiPut, apiDelete } from './client.js'

export function fetchInventorySummary(materialId) {
  return apiGet(`/inventory/summary/${materialId}`)
}

export function fetchInventoryItems(materialId, params = {}) {
  return apiGet(`/inventory/items/${materialId}`, params)
}

export function addInventoryItems(data) {
  return apiPost('/inventory/items', data)
}

export function deleteInventoryItem(id) {
  return apiDelete(`/inventory/items/${id}`)
}

export function createInventoryBatch(data) {
  return apiPost('/inventory/batches', data)
}

export function updateInventoryBatch(id, data) {
  return apiPut(`/inventory/batches/${id}`, data)
}

export function inbound(data) {
  return apiPost('/inbound', data)
}