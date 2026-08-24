import { apiGet, apiPost, apiPut } from './client.js'

export const stocktakeApi = {
  create: (note) => apiPost('/stocktake', { note }),
  list: () => apiGet('/stocktake'),
  detail: (id) => apiGet(`/stocktake/${id}`),
  updateEntry: (stocktakeId, entryId, body) => apiPut(`/stocktake/${stocktakeId}/entry/${entryId}`, body),
  complete: (stocktakeId, applyFix) => apiPost(`/stocktake/${stocktakeId}/complete?apply_fix=${applyFix ? 'true' : 'false'}`, {}),
}
