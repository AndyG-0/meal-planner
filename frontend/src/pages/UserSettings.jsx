import { useState, useEffect } from 'react'
import {
  Container,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  Card,
  CardContent,
  FormControlLabel,
  Switch,
} from '@mui/material'
import { Settings as SettingsIcon, Person as PersonIcon } from '@mui/icons-material'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'

export default function UserSettings() {
  const { user, setUser } = useAuthStore()
  const [preferences, setPreferences] = useState({
    calendar_start_day: 'sunday',
    theme: 'light',
  })
  const [dietaryPreferences, setDietaryPreferences] = useState([])
  const [calorieTarget, setCalorieTarget] = useState('')
  const [newDietaryPref, setNewDietaryPref] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const commonDietaryPrefs = [
    'Vegan',
    'Vegetarian',
    'Gluten-Free',
    'Dairy-Free',
    'Keto',
    'Paleo',
    'Low-Carb',
    'Halal',
    'Kosher',
  ]

  useEffect(() => {
    loadUserSettings()
  }, [])

  const loadUserSettings = async () => {
    try {
      const response = await api.get('/auth/me')
      const userData = response.data
      
      setPreferences(userData.preferences || { calendar_start_day: 'sunday', theme: 'light' })
      setDietaryPreferences(userData.dietary_preferences || [])
      setCalorieTarget(userData.calorie_target || '')
    } catch (err) {
      setError('Failed to load user settings')
    }
  }

  const handleUpdatePreferences = async () => {
    setLoading(true)
    setError('')
    setSuccess('')
    
    try {
      const response = await api.patch('/auth/me', {
        preferences,
        dietary_preferences: dietaryPreferences,
        calorie_target: calorieTarget ? parseInt(calorieTarget) : null,
      })
      
      setUser(response.data)
      setSuccess('Settings updated successfully!')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update settings')
    } finally {
      setLoading(false)
    }
  }

  const handleAddDietaryPref = () => {
    if (newDietaryPref && !dietaryPreferences.includes(newDietaryPref)) {
      setDietaryPreferences([...dietaryPreferences, newDietaryPref])
      setNewDietaryPref('')
    }
  }

  const handleRemoveDietaryPref = (pref) => {
    setDietaryPreferences(dietaryPreferences.filter(p => p !== pref))
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <SettingsIcon sx={{ mr: 1, fontSize: 32 }} />
          <Typography variant="h4">User Settings</Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
            {success}
          </Alert>
        )}

        {/* User Profile Section */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <PersonIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Profile Information</Typography>
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Username"
                  value={user?.username || ''}
                  disabled
                  helperText="Username cannot be changed"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Email"
                  value={user?.email || ''}
                  disabled
                  helperText="Email cannot be changed"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* General Preferences */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              General Preferences
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Calendar Start Day</InputLabel>
                  <Select
                    value={preferences.calendar_start_day || 'sunday'}
                    label="Calendar Start Day"
                    onChange={(e) =>
                      setPreferences({ ...preferences, calendar_start_day: e.target.value })
                    }
                  >
                    <MenuItem value="sunday">Sunday</MenuItem>
                    <MenuItem value="monday">Monday</MenuItem>
                    <MenuItem value="saturday">Saturday</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={preferences.theme || 'light'}
                    label="Theme"
                    onChange={(e) =>
                      setPreferences({ ...preferences, theme: e.target.value })
                    }
                  >
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="dark">Dark</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Dietary Preferences */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Dietary Preferences
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Select your dietary preferences to help the AI generate appropriate recipes for you.
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={preferences.use_dietary_preferences_in_ai !== false}
                  onChange={(e) =>
                    setPreferences({ ...preferences, use_dietary_preferences_in_ai: e.target.checked })
                  }
                />
              }
              label="Use dietary preferences when creating AI menu items"
              sx={{ mb: 2 }}
            />
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2, ml: 4 }}>
              When enabled, the AI will automatically apply your dietary preferences to all menu item suggestions unless you explicitly request otherwise.
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {dietaryPreferences.map((pref) => (
                <Chip
                  key={pref}
                  label={pref}
                  onDelete={() => handleRemoveDietaryPref(pref)}
                  color="primary"
                />
              ))}
            </Box>

            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <TextField
                label="Add dietary preference"
                value={newDietaryPref}
                onChange={(e) => setNewDietaryPref(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddDietaryPref()}
                size="small"
                fullWidth
              />
              <Button variant="outlined" onClick={handleAddDietaryPref}>
                Add
              </Button>
            </Box>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Quick add:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {commonDietaryPrefs
                .filter((pref) => !dietaryPreferences.includes(pref))
                .map((pref) => (
                  <Chip
                    key={pref}
                    label={pref}
                    onClick={() => setDietaryPreferences([...dietaryPreferences, pref])}
                    variant="outlined"
                    size="small"
                  />
                ))}
            </Box>
          </CardContent>
        </Card>

        {/* Calorie Target */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Calorie Target
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Set a daily calorie target to help the AI suggest recipes that fit your goals.
            </Typography>
            <TextField
              fullWidth
              label="Daily Calorie Target"
              type="number"
              value={calorieTarget}
              onChange={(e) => setCalorieTarget(e.target.value)}
              placeholder="e.g., 2000"
              helperText="Leave empty if you don't want to set a target"
            />
          </CardContent>
        </Card>

        {/* Save Button */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleUpdatePreferences}
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save Settings'}
          </Button>
        </Box>
      </Paper>
    </Container>
  )
}
