import { apiGet, apiPost } from './client.js'

export function fetchRestockSuggestions(windowDays = 30) {
  return apiGet('/reports/restock-suggestions', { window_days: windowDays })
}

export function fetchConsumptionTrends(materialId, months = 3) {
  return apiGet('/reports/consumption-trends', { material_id: materialId, months })
}

export function fetchDashboardAlerts(windowDays = 30) {
  return apiGet('/reports/dashboard-alerts', { window_days: windowDays })
}

export function fetchMaterialAlert(materialId, windowDays = 30) {
  return apiGet(`/reports/material-alert/${materialId}`, { window_days: windowDays })
}

export function sendReportEmail() {
  return apiPost('/reports/send-email')
}
