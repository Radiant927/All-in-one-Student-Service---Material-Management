export function isNonNegativeInteger(value) {
  return /^\d+$/.test(String(value).trim())
}

export function stocktakeProgress(counted, total) {
  if (!total) return 100
  return Math.round((counted / total) * 100)
}

export function filterStocktakeEntries(entries, filter) {
  if (filter === 'pending') return entries.filter(entry => !entry.counted)
  if (filter === 'discrepancy') return entries.filter(entry => entry.counted && entry.difference !== 0)
  return entries
}
