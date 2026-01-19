import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  Paper,
} from '@mui/material'
import api from '../services/api'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const [resetToken, setResetToken] = useState('')
  const [emailEnabled, setEmailEnabled] = useState(null)
  const [adminEmail, setAdminEmail] = useState('')
  const [configLoading, setConfigLoading] = useState(true)

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await api.get('/auth/password-reset-config')
        setEmailEnabled(response.data.email_enabled)
        setAdminEmail(response.data.admin_email)
      } catch (err) {
        console.error('Failed to fetch password reset config:', err)
        setEmailEnabled(false)
        setAdminEmail('admin')
      } finally {
        setConfigLoading(false)
      }
    }

    fetchConfig()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const response = await api.post('/auth/forgot-password', { email })
      setSuccess(response.data.message)
      
      // In development mode, the API returns the token
      if (response.data.token) {
        setResetToken(response.data.token)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send reset email')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Typography component="h1" variant="h5" align="center" gutterBottom>
            Forgot Password
          </Typography>

          {configLoading ? (
            <Alert severity="info">Loading...</Alert>
          ) : emailEnabled ? (
            <>
              <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 2 }}>
                Enter your email address and we&apos;ll send you a link to reset your password.
              </Typography>
              
              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}
              
              {success && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  {success}
                </Alert>
              )}

              {resetToken && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Development Mode:</strong> Use this link to reset your password:
                  </Typography>
                  <Link to={`/reset-password?token=${resetToken}`} style={{ wordBreak: 'break-all' }}>
                    Reset Password
                  </Link>
                </Alert>
              )}
              
              <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="email"
                  label="Email Address"
                  name="email"
                  autoComplete="email"
                  autoFocus
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  sx={{ mt: 3, mb: 2 }}
                  disabled={loading}
                >
                  {loading ? 'Sending...' : 'Send Reset Link'}
                </Button>
                <Box sx={{ textAlign: 'center' }}>
                  <Link to="/login" style={{ textDecoration: 'none' }}>
                    <Typography variant="body2" color="primary">
                      Back to Login
                    </Typography>
                  </Link>
                </Box>
              </Box>
            </>
          ) : (
            <>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  Password reset via email is not currently available.
                </Typography>
              </Alert>
              <Box sx={{ mt: 2, p: 2, backgroundColor: 'action.hover', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="body2" gutterBottom color="text.primary">
                  Please contact the administrator to reset your password:
                </Typography>
                <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold', color: 'primary.main' }}>
                  <a href={`mailto:${adminEmail}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                    {adminEmail}
                  </a>
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'center', mt: 3 }}>
                <Link to="/login" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" color="primary">
                    Back to Login
                  </Typography>
                </Link>
              </Box>
            </>
          )}
        </Paper>
      </Box>
    </Container>
  )
}
