import { Routes, Route, Navigate } from 'react-router-dom'
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
import { useAuthStore } from './store/authStore'

function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? children : <Navigate to="/login" />
}

function App() {
  return (
    <Routes>
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
