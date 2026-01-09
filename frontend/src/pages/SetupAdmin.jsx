import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  Paper,
  CircularProgress,
} from '@mui/material'
import { authService } from '../services'
import { useAuthStore } from '../store/authStore'
import { useSetupStore } from '../store/setupStore'

export default function SetupAdmin() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [checkingSetup, setCheckingSetup] = useState(true)
  const [setupRequired, setSetupRequired] = useState(false)
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const markSetupComplete = useSetupStore((state) => state.markSetupComplete)

  useEffect(() => {
    let isMounted = true

    const verifySetup = async () => {
      try {
        const { setup_required } = await authService.checkSetupRequired()

        if (!isMounted) return

        if (setup_required) {
          setSetupRequired(true)
        } else {
          navigate('/login', { replace: true })
        }
      } catch (err) {
        console.error('Error verifying setup status:', err)
        if (isMounted) {
          navigate('/login', { replace: true })
        }
      } finally {
        if (isMounted) {
          setCheckingSetup(false)
        }
      }
    }

    verifySetup()

    return () => {
      isMounted = false
    }
  }, [navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setLoading(true)

    try {
      // Create the initial admin user
      await authService.setupAdmin(username, email, password)
      
      // Log the user in automatically
      const loginData = await authService.login(username, password)
      
      // Fetch user details with admin flag
      const user = await authService.getCurrentUser()
      setAuth(user, loginData.access_token, loginData.refresh_token)
      
      // Only mark setup as complete after successful authentication
      markSetupComplete()
      
      // Navigate to dashboard
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Setup failed')
    } finally {
      setLoading(false)
    }
  }

  if (checkingSetup) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    )
  }

  if (!setupRequired) {
    // In case navigation hasn't occurred yet, avoid rendering the setup page
    return null
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
            Initial Setup
          </Typography>
          <Typography variant="body2" align="center" sx={{ mb: 2 }} color="text.secondary">
            Create the first admin account to get started
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Confirm Password"
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? 'Creating Admin Account...' : 'Create Admin Account'}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}
