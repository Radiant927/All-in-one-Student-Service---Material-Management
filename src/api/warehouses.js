import { apiGet, apiPost, apiPut, apiDelete } from './client.js'

export function fetchWarehouses() {
  return apiGet('/warehouses')
}

export function createWarehouse(data) {
  return apiPost('/warehouses', data)
}

export function fetchLocations(warehouseId) {
  return apiGet(`/warehouses/${warehouseId}/locations`)
}

export function fetchAllLocations() {
  return apiGet('/locations')
}

export function searchLocations(q) {
  return apiGet('/locations/search', { q })
}

export function createLocation(data) {
  return apiPost('/locations', data)
}

export function updateLocation(id, data) {
  return apiPut(`/locations/${id}`, data)
}

export function deleteLocation(id) {
  return apiDelete(`/locations/${id}`)
}