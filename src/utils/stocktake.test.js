import { describe, expect, it } from 'vitest'
import { filterStocktakeEntries, isNonNegativeInteger, stocktakeProgress } from './stocktake.js'

describe('stocktake helpers', () => {
  it('accepts only non-negative integer quantities', () => {
    expect(isNonNegativeInteger('0')).toBe(true)
    expect(isNonNegativeInteger('12')).toBe(true)
    expect(isNonNegativeInteger('-1')).toBe(false)
    expect(isNonNegativeInteger('1.5')).toBe(false)
    expect(isNonNegativeInteger('')).toBe(false)
  })

  it('calculates progress including empty snapshots', () => {
    expect(stocktakeProgress(2, 4)).toBe(50)
    expect(stocktakeProgress(0, 0)).toBe(100)
  })

  it('filters pending and discrepancy entries without treating pending as no-difference', () => {
    const entries = [
      { id: 1, counted: false, difference: 0 },
      { id: 2, counted: true, difference: 0 },
      { id: 3, counted: true, difference: -2 },
    ]
    expect(filterStocktakeEntries(entries, 'pending').map(item => item.id)).toEqual([1])
    expect(filterStocktakeEntries(entries, 'discrepancy').map(item => item.id)).toEqual([3])
  })
})
