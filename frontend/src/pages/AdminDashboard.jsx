import { useState, useEffect, useCallback } from 'react'
import {
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Button,
  Chip,
  Box,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  InputAdornment,
  CircularProgress,
} from '@mui/material'
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  AdminPanelSettings as AdminIcon,
  Group as GroupIcon,
  Restaurant as RestaurantIcon,
  CalendarMonth as CalendarIcon,
  Person as PersonIcon,
  RemoveRedEye as ViewIcon,
  Settings as SettingsIcon,
  SmartToy as AIIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'

function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

export default function AdminDashboard() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [recipes, setRecipes] = useState([])
  const [calendars, setCalendars] = useState([])
  const [groups, setGroups] = useState([])
  const [featureToggles, setFeatureToggles] = useState([])
  const [openaiSettings, setOpenaiSettings] = useState(null)
  const [sessionSettings, setSessionSettings] = useState(null)
  const [blockedDomains, setBlockedDomains] = useState([])
  const [newDomain, setNewDomain] = useState('')
  const [newDomainReason, setNewDomainReason] = useState('')
  const [availableModels, setAvailableModels] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [activeTab, setActiveTab] = useState(0)
  
  // Pagination state for recipes
  const [recipesSkip, setRecipesSkip] = useState(0)
  const [recipesHasMore, setRecipesHasMore] = useState(false)
  const [recipesLoading, setRecipesLoading] = useState(false)
  
  // Recipe filter states
  const [recipeSearch, setRecipeSearch] = useState('')
  const [recipeCategory, setRecipeCategory] = useState('')
  const [recipeDifficulty, setRecipeDifficulty] = useState('')
  const [recipeVisibility, setRecipeVisibility] = useState('')
  
  // Dialog states
  const [editUserDialog, setEditUserDialog] = useState(false)
  const [editRecipeDialog, setEditRecipeDialog] = useState(false)
  const [editCalendarDialog, setEditCalendarDialog] = useState(false)
  const [editGroupDialog, setEditGroupDialog] = useState(false)
  const [viewDetailsDialog, setViewDetailsDialog] = useState(false)
  
  // Edit states
  const [editingUser, setEditingUser] = useState(null)
  const [editingRecipe, setEditingRecipe] = useState(null)
  const [editingCalendar, setEditingCalendar] = useState(null)
  const [editingGroup, setEditingGroup] = useState(null)
  const [viewingDetails, setViewingDetails] = useState(null)

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      const limit = 100
      
      // Build filter params for recipes
      const recipeParams = { skip: 0, limit }
      if (recipeSearch) recipeParams.search = recipeSearch
      if (recipeCategory) recipeParams.category = recipeCategory
      if (recipeDifficulty) recipeParams.difficulty = recipeDifficulty
      if (recipeVisibility) recipeParams.visibility = recipeVisibility
      
      const [statsRes, usersRes, recipesRes, calendarsRes, groupsRes, togglesRes, openaiRes, sessionRes, blockedDomainsRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/users'),
        api.get('/admin/recipes', { params: recipeParams }),
        api.get('/admin/calendars'),
        api.get('/admin/groups'),
        api.get('/admin/feature-toggles'),
        api.get('/admin/openai-settings'),
        api.get('/admin/session-settings'),
        api.get('/admin/blocked-domains'),
      ])
      setStats(statsRes.data)
      setUsers(usersRes.data)
      setRecipes(recipesRes.data)
      setCalendars(calendarsRes.data)
      setGroups(groupsRes.data)
      setFeatureToggles(togglesRes.data)
      setOpenaiSettings(openaiRes.data)
      setSessionSettings(sessionRes.data)
      setBlockedDomains(blockedDomainsRes.data)
      
      // Set pagination state for recipes
      setRecipesSkip(limit)
      setRecipesHasMore(recipesRes.data.length === limit)
      
      // Load available OpenAI models
      try {
        const modelsRes = await api.get('/admin/openai-models')
        setAvailableModels(modelsRes.data.models || [])
      } catch (err) {
        console.error('Failed to load OpenAI models:', err)
        // Set default models if API call fails
        setAvailableModels([
          { id: 'gpt-4', name: 'GPT-4' },
          { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
          { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
        ])
      }
      
      setError('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load admin data')
    } finally {
      setLoading(false)
    }
  }, [recipeSearch, recipeCategory, recipeDifficulty, recipeVisibility])

  useEffect(() => {
    if (!user?.is_admin) {
      navigate('/')
      return
    }
    loadData()
  }, [user, navigate, loadData])

  const loadMoreRecipes = async () => {
    if (recipesLoading || !recipesHasMore) return
    
    try {
      setRecipesLoading(true)
      const limit = 100
      
      // Build filter params for recipes
      const recipeParams = { skip: recipesSkip, limit }
      if (recipeSearch) recipeParams.search = recipeSearch
      if (recipeCategory) recipeParams.category = recipeCategory
      if (recipeDifficulty) recipeParams.difficulty = recipeDifficulty
      if (recipeVisibility) recipeParams.visibility = recipeVisibility
      
      const recipesRes = await api.get('/admin/recipes', { params: recipeParams })
      
      setRecipes([...recipes, ...recipesRes.data])
      setRecipesSkip(recipesSkip + limit)
      setRecipesHasMore(recipesRes.data.length === limit)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load more recipes')
    } finally {
      setRecipesLoading(false)
    }
  }
  
  const handleRecipeFilterChange = () => {
    // Reset pagination and reload with filters
    setRecipesSkip(0)
    setRecipes([])
    loadData()
  }
  
  const handleClearRecipeFilters = () => {
    setRecipeSearch('')
    setRecipeCategory('')
    setRecipeDifficulty('')
    setRecipeVisibility('')
    setRecipesSkip(0)
    setRecipes([])
  }

  // User Management
  const handleEditUser = (u) => {
    setEditingUser({ id: u.id, email: u.email, is_admin: u.is_admin })
    setEditUserDialog(true)
  }

  const handleSaveUser = async () => {
    try {
      await api.patch(`/admin/users/${editingUser.id}`, {
        email: editingUser.email,
        is_admin: editingUser.is_admin,
      })
      await loadData()
      setEditUserDialog(false)
      setEditingUser(null)
      setSuccess('User updated successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update user')
    }
  }

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return
    try {
      await api.delete(`/admin/users/${userId}`)
      await loadData()
      setSuccess('User deleted successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete user')
    }
  }

  // Recipe Management
  const handleEditRecipe = (recipe) => {
    setEditingRecipe({
      id: recipe.id,
      title: recipe.title,
      description: recipe.description || '',
      visibility: recipe.visibility,
      difficulty: recipe.difficulty || 'easy',
    })
    setEditRecipeDialog(true)
  }

  const handleSaveRecipe = async () => {
    try {
      await api.patch(`/admin/recipes/${editingRecipe.id}`, {
        title: editingRecipe.title,
        description: editingRecipe.description,
        visibility: editingRecipe.visibility,
        difficulty: editingRecipe.difficulty,
      })
      await loadData()
      setEditRecipeDialog(false)
      setEditingRecipe(null)
      setSuccess('Recipe updated successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update recipe')
    }
  }

  const handleDeleteRecipe = async (recipeId) => {
    if (!window.confirm('Are you sure you want to delete this recipe?')) return
    try {
      await api.delete(`/admin/recipes/${recipeId}`)
      await loadData()
      setSuccess('Recipe deleted successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete recipe')
    }
  }

  const handleViewRecipe = async (recipeId) => {
    try {
      const res = await api.get(`/admin/recipes/${recipeId}`)
      setViewingDetails({ type: 'recipe', data: res.data })
      setViewDetailsDialog(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load recipe details')
    }
  }

  // Calendar Management
  const handleEditCalendar = (calendar) => {
    setEditingCalendar({
      id: calendar.id,
      name: calendar.name,
      visibility: calendar.visibility,
    })
    setEditCalendarDialog(true)
  }

  const handleSaveCalendar = async () => {
    try {
      await api.patch(`/admin/calendars/${editingCalendar.id}`, {
        name: editingCalendar.name,
        visibility: editingCalendar.visibility,
      })
      await loadData()
      setEditCalendarDialog(false)
      setEditingCalendar(null)
      setSuccess('Calendar updated successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update calendar')
    }
  }

  const handleDeleteCalendar = async (calendarId) => {
    if (!window.confirm('Are you sure you want to delete this calendar?')) return
    try {
      await api.delete(`/admin/calendars/${calendarId}`)
      await loadData()
      setSuccess('Calendar deleted successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete calendar')
    }
  }

  const handleViewCalendar = async (calendarId) => {
    try {
      const res = await api.get(`/admin/calendars/${calendarId}`)
      setViewingDetails({ type: 'calendar', data: res.data })
      setViewDetailsDialog(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load calendar details')
    }
  }

  // Group Management
  const handleEditGroup = (group) => {
    setEditingGroup({ id: group.id, name: group.name })
    setEditGroupDialog(true)
  }

  const handleSaveGroup = async () => {
    try {
      await api.patch(`/admin/groups/${editingGroup.id}`, {
        name: editingGroup.name,
      })
      await loadData()
      setEditGroupDialog(false)
      setEditingGroup(null)
      setSuccess('Group updated successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update group')
    }
  }

  const handleDeleteGroup = async (groupId) => {
    if (!window.confirm('Are you sure you want to delete this group?')) return
    try {
      await api.delete(`/admin/groups/${groupId}`)
      await loadData()
      setSuccess('Group deleted successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete group')
    }
  }

  const handleViewGroup = async (groupId) => {
    try {
      const res = await api.get(`/admin/groups/${groupId}`)
      setViewingDetails({ type: 'group', data: res.data })
      setViewDetailsDialog(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load group details')
    }
  }

  const handleRemoveGroupMember = async (groupId, memberId) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return
    try {
      await api.delete(`/admin/groups/${groupId}/members/${memberId}`)
      const res = await api.get(`/admin/groups/${groupId}`)
      setViewingDetails({ type: 'group', data: res.data })
      setSuccess('Member removed successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove member')
    }
  }

  // Feature Toggle Management
  const handleToggleFeature = async (featureKey, currentValue) => {
    try {
      await api.patch(`/admin/feature-toggles/${featureKey}`, {
        is_enabled: !currentValue,
      })
      await loadData()
      setSuccess(`Feature ${!currentValue ? 'enabled' : 'disabled'} successfully`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update feature toggle')
    }
  }

  // OpenAI Settings Management
  const handleUpdateOpenAISettings = async (settings) => {
    try {
      await api.patch('/admin/openai-settings', settings)
      await loadData()
      setSuccess('OpenAI settings updated successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update OpenAI settings')
    }
  }

  // Session Settings Management
  const handleUpdateSessionSettings = async (settings) => {
    try {
      await api.patch('/admin/session-settings', settings)
      await loadData()
      setSuccess('Session settings updated successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update session settings')
    }
  }

  // Blocked Domains Management
  const handleAddBlockedDomain = async () => {
    if (!newDomain.trim()) {
      setError('Domain cannot be empty')
      return
    }
    try {
      await api.post('/admin/blocked-domains', {
        domain: newDomain.trim(),
        reason: newDomainReason.trim() || 'Manually blocked'
      })
      setNewDomain('')
      setNewDomainReason('')
      await loadData()
      setSuccess('Domain blocked successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to block domain')
    }
  }

  const handleRemoveBlockedDomain = async (domainId) => {
    try {
      await api.delete(`/admin/blocked-domains/${domainId}`)
      await loadData()
      setSuccess('Domain unblocked successfully')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to unblock domain')
    }
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography>Loading...</Typography>
      </Container>
    )
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" alignItems="center" mb={3}>
        <AdminIcon sx={{ fontSize: 40, mr: 2 }} />
        <Typography variant="h4" component="h1">
          Admin Dashboard
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess('')} sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Total Users
                  </Typography>
                  <Typography variant="h4">{stats?.total_users || 0}</Typography>
                </div>
                <PersonIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Total Recipes
                  </Typography>
                  <Typography variant="h4">{stats?.total_recipes || 0}</Typography>
                </div>
                <RestaurantIcon sx={{ fontSize: 40, color: 'success.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Total Calendars
                  </Typography>
                  <Typography variant="h4">{stats?.total_calendars || 0}</Typography>
                </div>
                <CalendarIcon sx={{ fontSize: 40, color: 'info.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    Total Groups
                  </Typography>
                  <Typography variant="h4">{stats?.total_groups || 0}</Typography>
                </div>
                <GroupIcon sx={{ fontSize: 40, color: 'warning.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Version Info */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="textSecondary" gutterBottom>
                    App Version
                  </Typography>
                  <Typography variant="h4">{stats?.version || 'Loading...'}</Typography>
                </div>
                <InfoIcon sx={{ fontSize: 40, color: 'secondary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabbed Management Interface */}
      <Paper sx={{ width: '100%' }}>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
          <Tab label={`Users (${users.length})`} icon={<PersonIcon />} iconPosition="start" />
          <Tab label={`Menu Items (${recipes.length})`} icon={<RestaurantIcon />} iconPosition="start" />
          <Tab label={`Calendars (${calendars.length})`} icon={<CalendarIcon />} iconPosition="start" />
          <Tab label={`Groups (${groups.length})`} icon={<GroupIcon />} iconPosition="start" />
          <Tab label="Settings" icon={<SettingsIcon />} iconPosition="start" />
        </Tabs>

        {/* Users Tab */}
        <TabPanel value={activeTab} index={0}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Username</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Recipes</TableCell>
                  <TableCell>Calendars</TableCell>
                  <TableCell>Groups</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>{u.id}</TableCell>
                    <TableCell>{u.username}</TableCell>
                    <TableCell>{u.email}</TableCell>
                    <TableCell>
                      {u.is_admin ? (
                        <Chip label="Admin" color="primary" size="small" />
                      ) : (
                        <Chip label="User" size="small" />
                      )}
                    </TableCell>
                    <TableCell>{u.recipe_count}</TableCell>
                    <TableCell>{u.calendar_count}</TableCell>
                    <TableCell>{u.group_count}</TableCell>
                    <TableCell>{new Date(u.created_at).toLocaleDateString()}</TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => handleEditUser(u)} color="primary">
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteUser(u.id)}
                        color="error"
                        disabled={u.id === user?.id}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* Recipes Tab */}
        <TabPanel value={activeTab} index={1}>
          {/* Recipe Filters */}
          <Box sx={{ mb: 3 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Search menu items..."
                  value={recipeSearch}
                  onChange={(e) => setRecipeSearch(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleRecipeFilterChange()}
                />
              </Grid>
              
              <Grid item xs={12} sm={4} md={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={recipeCategory}
                    label="Category"
                    onChange={(e) => setRecipeCategory(e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="breakfast">Breakfast</MenuItem>
                    <MenuItem value="lunch">Lunch</MenuItem>
                    <MenuItem value="dinner">Dinner</MenuItem>
                    <MenuItem value="snack">Snack</MenuItem>
                    <MenuItem value="dessert">Dessert</MenuItem>
                    <MenuItem value="staple">Staple</MenuItem>
                    <MenuItem value="frozen">Frozen</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={4} md={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Difficulty</InputLabel>
                  <Select
                    value={recipeDifficulty}
                    label="Difficulty"
                    onChange={(e) => setRecipeDifficulty(e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="easy">Easy</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="hard">Hard</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={4} md={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Visibility</InputLabel>
                  <Select
                    value={recipeVisibility}
                    label="Visibility"
                    onChange={(e) => setRecipeVisibility(e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="public">Public</MenuItem>
                    <MenuItem value="group">Group</MenuItem>
                    <MenuItem value="private">Private</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6} md={1}>
                <Button
                  fullWidth
                  variant="contained"
                  size="small"
                  onClick={handleRecipeFilterChange}
                >
                  Search
                </Button>
              </Grid>
              
              <Grid item xs={12} sm={6} md={1}>
                <Button
                  fullWidth
                  variant="outlined"
                  size="small"
                  onClick={() => {
                    handleClearRecipeFilters()
                    handleRecipeFilterChange()
                  }}
                  disabled={!recipeSearch && !recipeCategory && !recipeDifficulty && !recipeVisibility}
                >
                  Clear
                </Button>
              </Grid>
            </Grid>
          </Box>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Owner</TableCell>
                  <TableCell>Visibility</TableCell>
                  <TableCell>Difficulty</TableCell>
                  <TableCell>Time</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recipes.map((recipe) => (
                  <TableRow key={recipe.id}>
                    <TableCell>{recipe.id}</TableCell>
                    <TableCell>{recipe.title}</TableCell>
                    <TableCell>{recipe.owner_username}</TableCell>
                    <TableCell>
                      <Chip 
                        label={recipe.visibility} 
                        size="small"
                        color={
                          recipe.visibility === 'public' ? 'success' :
                          recipe.visibility === 'group' ? 'info' : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell>
                      {recipe.difficulty ? (
                        <Chip 
                          label={recipe.difficulty} 
                          size="small"
                          color={
                            recipe.difficulty === 'easy' ? 'success' :
                            recipe.difficulty === 'medium' ? 'warning' : 'error'
                          }
                        />
                      ) : '-'}
                    </TableCell>
                    <TableCell>
                      {recipe.prep_time || 0}m / {recipe.cook_time || 0}m
                    </TableCell>
                    <TableCell>{new Date(recipe.created_at).toLocaleDateString()}</TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => handleViewRecipe(recipe.id)} color="info">
                        <ViewIcon />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleEditRecipe(recipe)} color="primary">
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDeleteRecipe(recipe.id)} color="error">
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {/* Load More button for recipes */}
          {recipesHasMore && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Button
                variant="outlined"
                onClick={loadMoreRecipes}
                disabled={recipesLoading}
                size="large"
              >
                {recipesLoading ? <CircularProgress size={24} /> : `Load More Recipes (${recipes.length} of ${stats?.total_recipes || 0})`}
              </Button>
            </Box>
          )}
          
          {!recipesHasMore && recipes.length > 0 && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Typography variant="body2" color="text.secondary">
                Showing all {recipes.length} recipes
              </Typography>
            </Box>
          )}
        </TabPanel>

        {/* Calendars Tab */}
        <TabPanel value={activeTab} index={2}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Owner</TableCell>
                  <TableCell>Visibility</TableCell>
                  <TableCell>Group</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {calendars.map((calendar) => (
                  <TableRow key={calendar.id}>
                    <TableCell>{calendar.id}</TableCell>
                    <TableCell>{calendar.name}</TableCell>
                    <TableCell>{calendar.owner_username}</TableCell>
                    <TableCell>
                      <Chip 
                        label={calendar.visibility} 
                        size="small"
                        color={
                          calendar.visibility === 'public' ? 'success' :
                          calendar.visibility === 'group' ? 'info' : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell>{calendar.group_id || '-'}</TableCell>
                    <TableCell>{new Date(calendar.created_at).toLocaleDateString()}</TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => handleViewCalendar(calendar.id)} color="info">
                        <ViewIcon />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleEditCalendar(calendar)} color="primary">
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDeleteCalendar(calendar.id)} color="error">
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* Groups Tab */}
        <TabPanel value={activeTab} index={3}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Owner</TableCell>
                  <TableCell>Members</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {groups.map((group) => (
                  <TableRow key={group.id}>
                    <TableCell>{group.id}</TableCell>
                    <TableCell>{group.name}</TableCell>
                    <TableCell>{group.owner_username}</TableCell>
                    <TableCell>{group.member_count}</TableCell>
                    <TableCell>{new Date(group.created_at).toLocaleDateString()}</TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => handleViewGroup(group.id)} color="info">
                        <ViewIcon />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleEditGroup(group)} color="primary">
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDeleteGroup(group.id)} color="error">
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* Settings Tab */}
        <TabPanel value={activeTab} index={4}>
          <Grid container spacing={3}>
            {/* Feature Toggles Section */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <SettingsIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Feature Toggles</Typography>
                  </Box>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Feature</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {featureToggles.map((toggle) => (
                        <TableRow key={toggle.id}>
                          <TableCell>
                            <Typography variant="subtitle2">{toggle.feature_name}</Typography>
                            <Typography variant="caption" color="textSecondary">
                              {toggle.feature_key}
                            </Typography>
                          </TableCell>
                          <TableCell>{toggle.description}</TableCell>
                          <TableCell>
                            <Chip
                              label={toggle.is_enabled ? 'Enabled' : 'Disabled'}
                              color={toggle.is_enabled ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <FormControlLabel
                              control={
                                <Switch
                                  checked={toggle.is_enabled}
                                  onChange={() => handleToggleFeature(toggle.feature_key, toggle.is_enabled)}
                                />
                              }
                              label=""
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </Grid>

            {/* OpenAI Settings Section */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <AIIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">OpenAI Configuration</Typography>
                  </Box>
                  {openaiSettings && (
                    <Box component="form" sx={{ mt: 2 }}>
                      <TextField
                        fullWidth
                        label="API Key"
                        type="password"
                        value={openaiSettings.api_key || ''}
                        onChange={(e) => setOpenaiSettings({ ...openaiSettings, api_key: e.target.value })}
                        margin="normal"
                        placeholder="sk-..."
                        helperText={openaiSettings.has_api_key ? "API key is set (enter new key to update)" : "Your OpenAI API key (kept secure)"}
                        InputProps={{
                          endAdornment: openaiSettings.has_api_key && (
                            <InputAdornment position="end">
                              <CheckCircleIcon color="success" titleAccess="API key is configured" />
                            </InputAdornment>
                          ),
                        }}
                      />
                      <FormControl fullWidth margin="normal">
                        <InputLabel id="model-select-label">Model</InputLabel>
                        <Select
                          labelId="model-select-label"
                          label="Model"
                          value={openaiSettings.model || 'gpt-4'}
                          onChange={(e) => setOpenaiSettings({ ...openaiSettings, model: e.target.value })}
                        >
                          {availableModels.length > 0 ? (
                            availableModels.map((model) => (
                              <MenuItem key={model.id} value={model.id}>
                                {model.name || model.id}
                              </MenuItem>
                            ))
                          ) : (
                            [
                              <MenuItem key="gpt-4" value="gpt-4">GPT-4</MenuItem>,
                              <MenuItem key="gpt-4-turbo" value="gpt-4-turbo">GPT-4 Turbo</MenuItem>,
                              <MenuItem key="gpt-3.5-turbo" value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>,
                            ]
                          )}
                        </Select>
                      </FormControl>
                      <TextField
                        fullWidth
                        label="System Prompt"
                        multiline
                        rows={6}
                        value={openaiSettings.system_prompt || ''}
                        onChange={(e) => setOpenaiSettings({ ...openaiSettings, system_prompt: e.target.value })}
                        margin="normal"
                        helperText="Instructions for the AI assistant"
                      />
                      <TextField
                        fullWidth
                        label="SEARXNG URL"
                        value={openaiSettings.searxng_url || 'http://localhost:8085'}
                        onChange={(e) => setOpenaiSettings({ ...openaiSettings, searxng_url: e.target.value })}
                        margin="normal"
                        helperText="URL for SEARXNG search engine (used for web search and recipe import)"
                      />
                      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                        <Button
                          variant="contained"
                          onClick={() => handleUpdateOpenAISettings(openaiSettings)}
                        >
                          Save OpenAI Settings
                        </Button>
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Session Settings Section */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <SettingsIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Session Settings</Typography>
                  </Box>
                  {sessionSettings && (
                    <Box component="form" sx={{ mt: 2 }}>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                        Configure how long user sessions remain active before requiring re-authentication.
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                        <TextField
                          label="Session Duration"
                          type="number"
                          value={sessionSettings.session_ttl_value || 90}
                          onChange={(e) => setSessionSettings({ ...sessionSettings, session_ttl_value: parseInt(e.target.value) || 1 })}
                          margin="normal"
                          inputProps={{ min: 1, max: 365 }}
                          sx={{ flexGrow: 1 }}
                          helperText="Enter a value between 1 and 365"
                        />
                        <FormControl margin="normal" sx={{ minWidth: 120 }}>
                          <InputLabel id="session-unit-label">Unit</InputLabel>
                          <Select
                            labelId="session-unit-label"
                            label="Unit"
                            value={sessionSettings.session_ttl_unit || 'days'}
                            onChange={(e) => setSessionSettings({ ...sessionSettings, session_ttl_unit: e.target.value })}
                          >
                            <MenuItem value="minutes">Minutes</MenuItem>
                            <MenuItem value="hours">Hours</MenuItem>
                            <MenuItem value="days">Days</MenuItem>
                          </Select>
                        </FormControl>
                      </Box>
                      <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                        Current setting: {sessionSettings.session_ttl_value} {sessionSettings.session_ttl_unit}
                        {sessionSettings.updated_at && ` (Last updated: ${new Date(sessionSettings.updated_at).toLocaleString()})`}
                      </Typography>
                      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                        <Button
                          variant="contained"
                          onClick={() => handleUpdateSessionSettings(sessionSettings)}
                        >
                          Save Session Settings
                        </Button>
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Blocked Image Domains Section */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <SettingsIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Image Download Block List</Typography>
                  </Box>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    Domains that are blocked from being used as image sources. Images from these domains cannot be downloaded.
                  </Typography>
                  
                  {/* Add New Domain Form */}
                  <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                    <TextField
                      label="Domain"
                      value={newDomain}
                      onChange={(e) => setNewDomain(e.target.value)}
                      placeholder="example.com"
                      sx={{ flexGrow: 1 }}
                      size="small"
                    />
                    <TextField
                      label="Reason (optional)"
                      value={newDomainReason}
                      onChange={(e) => setNewDomainReason(e.target.value)}
                      placeholder="Why is this domain blocked?"
                      sx={{ flexGrow: 2 }}
                      size="small"
                    />
                    <Button
                      variant="contained"
                      onClick={handleAddBlockedDomain}
                      sx={{ whiteSpace: 'nowrap' }}
                    >
                      Block Domain
                    </Button>
                  </Box>

                  {/* Blocked Domains Table */}
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Domain</TableCell>
                          <TableCell>Reason</TableCell>
                          <TableCell>Blocked At</TableCell>
                          <TableCell align="right">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {blockedDomains.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={4} align="center">
                              <Typography variant="body2" color="textSecondary">
                                No domains blocked yet
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ) : (
                          blockedDomains.map((domain) => (
                            <TableRow key={domain.id}>
                              <TableCell>
                                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                  {domain.domain}
                                </Typography>
                              </TableCell>
                              <TableCell>{domain.reason || 'No reason provided'}</TableCell>
                              <TableCell>
                                {new Date(domain.created_at).toLocaleDateString()}
                              </TableCell>
                              <TableCell align="right">
                                <IconButton
                                  size="small"
                                  onClick={() => handleRemoveBlockedDomain(domain.id)}
                                  color="error"
                                  title="Unblock this domain"
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Edit User Dialog */}
      <Dialog open={editUserDialog} onClose={() => setEditUserDialog(false)}>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Email"
            value={editingUser?.email || ''}
            onChange={(e) => setEditingUser({ ...editingUser, email: e.target.value })}
            margin="normal"
            type="email"
          />
          <FormControlLabel
            control={
              <Switch
                checked={editingUser?.is_admin || false}
                onChange={(e) => setEditingUser({ ...editingUser, is_admin: e.target.checked })}
              />
            }
            label="Administrator"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditUserDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveUser} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Recipe Dialog */}
      <Dialog open={editRecipeDialog} onClose={() => setEditRecipeDialog(false)}>
        <DialogTitle>Edit Recipe</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Title"
            value={editingRecipe?.title || ''}
            onChange={(e) => setEditingRecipe({ ...editingRecipe, title: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Description"
            value={editingRecipe?.description || ''}
            onChange={(e) => setEditingRecipe({ ...editingRecipe, description: e.target.value })}
            margin="normal"
            multiline
            rows={3}
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Visibility</InputLabel>
            <Select
              value={editingRecipe?.visibility || 'private'}
              label="Visibility"
              onChange={(e) => setEditingRecipe({ ...editingRecipe, visibility: e.target.value })}
            >
              <MenuItem value="private">Private</MenuItem>
              <MenuItem value="group">Group</MenuItem>
              <MenuItem value="public">Public</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel>Difficulty</InputLabel>
            <Select
              value={editingRecipe?.difficulty || 'easy'}
              label="Difficulty"
              onChange={(e) => setEditingRecipe({ ...editingRecipe, difficulty: e.target.value })}
            >
              <MenuItem value="easy">Easy</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="hard">Hard</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditRecipeDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveRecipe} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Calendar Dialog */}
      <Dialog open={editCalendarDialog} onClose={() => setEditCalendarDialog(false)}>
        <DialogTitle>Edit Calendar</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={editingCalendar?.name || ''}
            onChange={(e) => setEditingCalendar({ ...editingCalendar, name: e.target.value })}
            margin="normal"
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Visibility</InputLabel>
            <Select
              value={editingCalendar?.visibility || 'private'}
              label="Visibility"
              onChange={(e) => setEditingCalendar({ ...editingCalendar, visibility: e.target.value })}
            >
              <MenuItem value="private">Private</MenuItem>
              <MenuItem value="group">Group</MenuItem>
              <MenuItem value="public">Public</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditCalendarDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveCalendar} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Group Dialog */}
      <Dialog open={editGroupDialog} onClose={() => setEditGroupDialog(false)}>
        <DialogTitle>Edit Group</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={editingGroup?.name || ''}
            onChange={(e) => setEditingGroup({ ...editingGroup, name: e.target.value })}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditGroupDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveGroup} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* View Details Dialog */}
      <Dialog 
        open={viewDetailsDialog} 
        onClose={() => setViewDetailsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {viewingDetails?.type === 'recipe' && 'Recipe Details'}
          {viewingDetails?.type === 'calendar' && 'Calendar Details'}
          {viewingDetails?.type === 'group' && 'Group Details'}
        </DialogTitle>
        <DialogContent>
          {viewingDetails?.type === 'recipe' && (
            <Box>
              <Typography variant="h6">{viewingDetails.data.title}</Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Owner: {viewingDetails.data.owner_username}
              </Typography>
              <Typography variant="body2" sx={{ mt: 2 }}>
                {viewingDetails.data.description}
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2">Ingredients:</Typography>
                <ul>
                  {viewingDetails.data.ingredients?.map((ing, idx) => (
                    <li key={idx}>
                      {ing.quantity} {ing.unit} {ing.name}
                    </li>
                  ))}
                </ul>
              </Box>
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2">Instructions:</Typography>
                <ol>
                  {viewingDetails.data.instructions?.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ol>
              </Box>
            </Box>
          )}

          {viewingDetails?.type === 'calendar' && (
            <Box>
              <Typography variant="h6">{viewingDetails.data.name}</Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Owner: {viewingDetails.data.owner_username}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Visibility: {viewingDetails.data.visibility}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Total Meals: {viewingDetails.data.meal_count}
              </Typography>
            </Box>
          )}

          {viewingDetails?.type === 'group' && (
            <Box>
              <Typography variant="h6">{viewingDetails.data.name}</Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Owner: {viewingDetails.data.owner_username}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Recipes: {viewingDetails.data.recipe_count}
              </Typography>
              <Typography variant="body2">
                Calendars: {viewingDetails.data.calendar_count}
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2">Members:</Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Username</TableCell>
                      <TableCell>Role</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {viewingDetails.data.members?.map((member) => (
                      <TableRow key={member.id}>
                        <TableCell>{member.username}</TableCell>
                        <TableCell>
                          <Chip 
                            label={member.role} 
                            size="small"
                            color={member.role === 'admin' ? 'primary' : 'default'}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => handleRemoveGroupMember(viewingDetails.data.id, member.id)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}
