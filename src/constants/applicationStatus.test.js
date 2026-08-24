import { describe, expect, it } from 'vitest'
import { applicationStatusLabel } from './applicationStatus.js'

describe('applicationStatusLabel', () => {
  it('uses the shared team vocabulary', () => {
    expect(applicationStatusLabel('approved')).toBe('待领取')
    expect(applicationStatusLabel('return_pending')).toBe('待归还验收')
  })
})

