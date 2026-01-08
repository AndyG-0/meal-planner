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
import GroceryList from './pages/GroceryList'
import Groups from './pages/Groups'
import AdminDashboard from './pages/AdminDashboard'
import UserSettings from './pages/UserSettings'
import Collections from './pages/Collections'
import SetupAdmin from './pages/SetupAdmin'
import { useAuthStore } from './store/authStore'
import { useSetupStore } from './store/setupStore'
import { authService } from './services'
import { CircularProgress, Box } from '@mui/material'

function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? children : <Navigate to="/login" />
}

function App() {
  const [checkingSetup, setCheckingSetup] = useState(true)
  const setupComplete = useSetupStore((state) => state.setupComplete)
  const markSetupComplete = useSetupStore((state) => state.markSetupComplete)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
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
            navigate('/setup')
          }
        } else {
          // If there are users but setupComplete isn't set, mark it as complete
          markSetupComplete()
        }
      } catch (error) {
        console.error('Error checking setup status:', error)
      } finally {
        setCheckingSetup(false)
      }
    }

    checkSetup()
  }, [setupComplete, markSetupComplete, navigate, location.pathname])

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
      <Route path="/setup" element={<SetupAdmin />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="recipes" element={<ProtectedRoute><Recipes /></ProtectedRoute>} />
        <Route path="calendar" element={<ProtectedRoute><Calendar /></ProtectedRoute>} />
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
