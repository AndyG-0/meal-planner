import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Box, CircularProgress, Alert, Typography, Button } from '@mui/material'
import { CheckCircle, Error } from '@mui/icons-material'
import { krogerService } from '../services'
import { getErrorMessage } from '../utils/errorHandler'

export default function KrogerCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState('processing') // processing, success, error
  const [error, setError] = useState(null)

  useEffect(() => {
    handleCallback()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleCallback = async () => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const errorParam = searchParams.get('error')
    const errorDescription = searchParams.get('error_description')

    // Handle authorization errors
    if (errorParam) {
      setStatus('error')
      setError(errorDescription || `Authorization failed: ${errorParam}`)
      return
    }

    // Validate required parameters
    if (!code || !state) {
      setStatus('error')
      setError('Missing authorization code or state parameter')
      return
    }

    try {
      await krogerService.handleCallback(code, state)
      setStatus('success')
      
      // Redirect to grocery lists after 2 seconds
      setTimeout(() => {
        navigate('/grocery-lists')
      }, 2000)
    } catch (err) {
      setStatus('error')
      setError(
        getErrorMessage(
          err.response?.data?.detail,
          'Failed to complete Kroger authorization'
        )
      )
    }
  }

  const handleRetry = () => {
    navigate('/grocery-lists')
  }

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      p={3}
    >
      {status === 'processing' && (
        <>
          <CircularProgress size={60} sx={{ mb: 3 }} />
          <Typography variant="h5" gutterBottom>
            Connecting to Kroger...
          </Typography>
          <Typography color="text.secondary">
            Please wait while we complete the authorization
          </Typography>
        </>
      )}

      {status === 'success' && (
        <>
          <CheckCircle color="success" sx={{ fontSize: 80, mb: 3 }} />
          <Typography variant="h5" gutterBottom>
            Successfully Connected!
          </Typography>
          <Typography color="text.secondary" gutterBottom>
            Your Kroger account has been linked
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Redirecting to grocery lists...
          </Typography>
        </>
      )}

      {status === 'error' && (
        <>
          <Error color="error" sx={{ fontSize: 80, mb: 3 }} />
          <Typography variant="h5" gutterBottom>
            Authorization Failed
          </Typography>
          <Alert severity="error" sx={{ mb: 3, maxWidth: 500 }}>
            {error}
          </Alert>
          <Button variant="contained" onClick={handleRetry}>
            Return to Grocery Lists
          </Button>
        </>
      )}
    </Box>
  )
}
