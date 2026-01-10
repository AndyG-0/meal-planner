import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Dashboard from './pages/Dashboard'
import Recipes from './pages/Recipes'
import Calendar from './pages/Calendar'
import CalendarManagement from './pages/CalendarManagement'
import GroceryList from './pages/GroceryList'
import Groups from './pages/Groups'
import AdminDashboard from './pages/AdminDashboard'
import UserSettings from './pages/UserSettings'
import Collections from './pages/Collections'
import SetupAdmin from './pages/SetupAdmin'
import { useAuthStore } from './store/authStore'
import { useSetupStore } from './store/setupStore'
import { authService } from './services'
import { CircularProgress, Box, Alert, Button } from '@mui/material'

function SetupRoute() {
  const setupComplete = useSetupStore((state) => state.setupComplete)
  return setupComplete ? <Navigate to="/login" replace /> : <SetupAdmin />
}

function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? children : <Navigate to="/login" />
}

function App() {
  const [checkingSetup, setCheckingSetup] = useState(true)
  const [setupError, setSetupError] = useState(null)
  const setupComplete = useSetupStore((state) => state.setupComplete)
  const markSetupComplete = useSetupStore((state) => state.markSetupComplete)
  const navigate = useNavigate()
  const location = useLocation()

  const retrySetupCheck = () => {
    setSetupError(null)
    setCheckingSetup(true)
    checkSetup()
  }

  const checkSetup = async () => {
    // If setup is already marked as complete in localStorage, skip the check
    if (setupComplete) {
      setCheckingSetup(false)
      return
    }

    try {
      const { setup_required } = await authService.checkSetupRequired()
      
      if (setup_required) {
        // Redirect to setup page if not already there
        if (location.pathname !== '/setup') {
          navigate('/setup', { replace: true })
        }
      } else {
        // If there are users but setupComplete isn't set, mark it as complete
        markSetupComplete()
      }
      setSetupError(null)
    } catch (error) {
      console.error('Error checking setup status:', error)
      setSetupError('Unable to connect to the server. Please check your connection and try again.')
    } finally {
      setCheckingSetup(false)
    }
  }

  useEffect(() => {
    checkSetup()
  // location.pathname intentionally excluded to prevent re-checking on navigation
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setupComplete, markSetupComplete, navigate])

  if (setupError) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          p: 3,
        }}
      >
        <Alert 
          severity="error" 
          sx={{ mb: 2, maxWidth: 500 }}
          action={
            <Button color="inherit" size="small" onClick={retrySetupCheck}>
              Retry
            </Button>
          }
        >
          {setupError}
        </Alert>
      </Box>
    )
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

  return (
    <Routes>
      <Route path="/setup" element={<SetupRoute />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="recipes" element={<ProtectedRoute><Recipes /></ProtectedRoute>} />
        <Route path="calendar" element={<ProtectedRoute><Calendar /></ProtectedRoute>} />
        <Route path="calendar-management" element={<ProtectedRoute><CalendarManagement /></ProtectedRoute>} />
        <Route path="grocery-lists" element={<ProtectedRoute><GroceryList /></ProtectedRoute>} />
        <Route path="groups" element={<ProtectedRoute><Groups /></ProtectedRoute>} />
        <Route path="collections" element={<ProtectedRoute><Collections /></ProtectedRoute>} />
        <Route path="settings" element={<ProtectedRoute><UserSettings /></ProtectedRoute>} />
        <Route path="admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
      </Route>
    </Routes>
  )
}

export default App
