import { apiGet, apiPost } from './client.js'

export function fetchBorrowApplications(params = {}) {
  return apiGet('/borrow-applications', params)
}

export function approveBorrowApplication(id, note = '', reservationHours = 48) {
  return apiPost(`/borrow-applications/${id}/approve`, {
    note,
    reservation_hours: reservationHours,
  })
}

export function rejectBorrowApplication(id, note = '') {
  return apiPost(`/borrow-applications/${id}/reject`, { note, reservation_hours: 48 })
}

export function confirmPickup(id, idempotencyKey, warehouseId = null) {
  return apiPost(`/borrow-applications/${id}/confirm-pickup`, {
    idempotency_key: idempotencyKey,
    warehouse_id: warehouseId,
  })
}

export function confirmReturn(id, idempotencyKey, warehouseId = null) {
  return apiPost(`/borrow-applications/${id}/confirm-return`, {
    idempotency_key: idempotencyKey,
    warehouse_id: warehouseId,
  })
}

export function resolveScan(payload) {
  return apiPost('/scan/resolve', { payload })
}

