import { Routes, Route, Navigate } from 'react-router-dom'
import { Container } from '@mui/material'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Recipes from './pages/Recipes'
import Calendar from './pages/Calendar'
import GroceryList from './pages/GroceryList'
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
      <Route path="/" element={<Layout />}>
        <Route index element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="recipes" element={<ProtectedRoute><Recipes /></ProtectedRoute>} />
        <Route path="calendar" element={<ProtectedRoute><Calendar /></ProtectedRoute>} />
        <Route path="grocery-list" element={<ProtectedRoute><GroceryList /></ProtectedRoute>} />
      </Route>
    </Routes>
  )
}

export default App
