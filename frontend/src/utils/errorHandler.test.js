import { describe, it, expect } from 'vitest'
import { getErrorMessage } from './errorHandler'

describe('getErrorMessage', () => {
  it('should return string error messages as-is', () => {
    const result = getErrorMessage('Simple error message')
    expect(result).toBe('Simple error message')
  })

  it('should handle Pydantic validation error arrays', () => {
    const validationErrors = [
      { type: 'value_error', loc: ['field1'], msg: 'Field is required', input: {} },
      { type: 'value_error', loc: ['field2'], msg: 'Invalid format', input: {} },
    ]
    const result = getErrorMessage(validationErrors)
    expect(result).toBe('Field is required')
  })

  it('should handle single Pydantic validation error object', () => {
    const error = { type: 'value_error', loc: ['meal_type'], msg: 'Invalid meal type', input: {} }
    const result = getErrorMessage(error)
    expect(result).toBe('Invalid meal type')
  })

  it('should return fallback message for unknown object types', () => {
    const result = getErrorMessage({ some: 'object' }, 'Custom fallback')
    expect(result).toBe('Custom fallback')
  })

  it('should return default fallback when no message can be extracted', () => {
    const result = getErrorMessage({})
    expect(result).toBe('An error occurred')
  })

  it('should handle empty arrays', () => {
    const result = getErrorMessage([], 'No errors')
    expect(result).toBe('No errors')
  })

  it('should handle array of strings', () => {
    const result = getErrorMessage(['First error', 'Second error'])
    expect(result).toBe('First error')
  })

  it('should handle null/undefined gracefully', () => {
    expect(getErrorMessage(null, 'Fallback')).toBe('Fallback')
    expect(getErrorMessage(undefined, 'Fallback')).toBe('Fallback')
  })
})
