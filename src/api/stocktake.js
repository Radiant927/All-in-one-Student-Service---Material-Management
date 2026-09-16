import { apiDelete, apiGet, apiPost, apiPut } from './client.js'

export const stocktakeApi = {
  create: (note) => apiPost('/stocktake', { note }),
  list: () => apiGet('/stocktake'),
  detail: (id) => apiGet(`/stocktake/${id}`),
  updateEntry: (stocktakeId, entryId, body) => apiPut(`/stocktake/${stocktakeId}/entry/${entryId}`, body),
  addSurplusEntry: (stocktakeId, body) => apiPost(`/stocktake/${stocktakeId}/entries`, body),
  scanItem: (stocktakeId, entryId, payload) => apiPost(`/stocktake/${stocktakeId}/entry/${entryId}/scan`, { payload }),
  undoScan: (stocktakeId, entryId, checkId) => apiDelete(`/stocktake/${stocktakeId}/entry/${entryId}/scan/${checkId}`),
  confirmEntry: (stocktakeId, entryId) => apiPost(`/stocktake/${stocktakeId}/entry/${entryId}/confirm`, {}),
  complete: (stocktakeId, applyFix) => apiPost(`/stocktake/${stocktakeId}/complete?apply_fix=${applyFix ? 'true' : 'false'}`, {}),
  cancel: (stocktakeId) => apiPost(`/stocktake/${stocktakeId}/cancel`, {}),
}
