/**
 * Extracts a user-friendly error message from various error response formats
 * Handles:
 * - String messages
 * - Pydantic validation errors (array of error objects)
 * - Error objects with detail property
 * 
 * @param {any} errorData - The error data from response
 * @param {string} fallbackMessage - Default message if extraction fails
 * @returns {string} A user-friendly error message
 */
export function getErrorMessage(errorData, fallbackMessage = 'An error occurred') {
  // If it's a string, return it directly
  if (typeof errorData === 'string') {
    return errorData
  }

  // If it's an array (Pydantic validation errors), extract the first meaningful message
  if (Array.isArray(errorData)) {
    if (errorData.length > 0) {
      const firstError = errorData[0]
      // Pydantic error format: { type, loc, msg, input }
      if (firstError.msg) {
        return firstError.msg
      }
      // Fallback to string representation if available
      if (typeof firstError === 'string') {
        return firstError
      }
    }
    return fallbackMessage
  }

  // If it's an object with a msg property (single Pydantic error)
  if (errorData && typeof errorData === 'object' && errorData.msg) {
    return errorData.msg
  }

  // Fallback to fallback message
  return fallbackMessage
}
