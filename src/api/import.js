import { apiUpload } from './client.js'

export function importExcel(file) {
  return apiUpload('/import/excel', file)
}