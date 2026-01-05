import { useState, useEffect } from 'react'
import { 
  Typography, 
  Grid, 
  Paper, 
  Box, 
  Card, 
  CardContent, 
  List, 
  ListItem, 
  ListItemText,
  ListItemIcon,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Divider
} from '@mui/material'
import { 
  Restaurant, 
  CalendarMonth, 
  ShoppingCart, 
  Favorite,
  TrendingUp,
  Event,
  AccessTime,
  Help as HelpIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { format, isToday, isTomorrow, parseISO } from 'date-fns'
import { recipeService, calendarService, groceryListService } from '../services'
import OnboardingTutorial from '../components/OnboardingTutorial'

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({
    totalRecipes: 0,
    favoriteRecipes: 0,
    recentRecipes: [],
  })
  const [upcomingMeals, setUpcomingMeals] = useState([])
  const [groceryLists, setGroceryLists] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [tutorialOpen, setTutorialOpen] = useState(false)

  useEffect(() => {
    loadDashboardData()
    
    // Check if user has seen the tutorial
    const tutorialCompleted = localStorage.getItem('tutorialCompleted')
    if (!tutorialCompleted) {
      setTutorialOpen(true)
    }
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      // Load recipes
      const response = await recipeService.getRecipes({ page_size: 100 })
      // Backend now returns paginated response: { items: [], pagination: {} }
      const recipes = response.items || []
      const favoriteCount = recipes.filter(r => r.is_favorite).length
      const sortedRecipes = [...recipes].sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
      )
      
      setStats({
        totalRecipes: response.pagination?.total || recipes.length,
        favoriteRecipes: favoriteCount,
        recentRecipes: sortedRecipes.slice(0, 3),
      })

      // Load upcoming meals
      const calendars = await calendarService.getCalendars()
      if (calendars.length > 0) {
        const today = new Date()
        const nextWeek = new Date(today)
        nextWeek.setDate(today.getDate() + 7)
        
        const meals = await calendarService.getCalendarMeals(calendars[0].id, {
          start_date: today.toISOString(),
          end_date: nextWeek.toISOString(),
        })
        
        const sortedMeals = meals
          .sort((a, b) => new Date(a.meal_date) - new Date(b.meal_date))
          .slice(0, 5)
        setUpcomingMeals(sortedMeals)
      }

      // Load grocery lists
      const lists = await groceryListService.getGroceryLists()
      setGroceryLists(lists)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const formatMealDate = (dateString) => {
    if (!dateString) return 'No date'
    try {
      const date = parseISO(dateString)
      if (isNaN(date.getTime())) return 'Invalid date'
      if (isToday(date)) return 'Today'
      if (isTomorrow(date)) return 'Tomorrow'
      return format(date, 'EEE, MMM d')
    } catch (error) {
      console.error('Date parsing error:', error, dateString)
      return 'Invalid date'
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<HelpIcon />}
          onClick={() => setTutorialOpen(true)}
        >
          Tutorial
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              cursor: 'pointer',
              '&:hover': { bgcolor: 'action.hover' },
              transition: 'background-color 0.2s',
            }}
            onClick={() => navigate('/recipes')}
          >
            <Restaurant sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h3" fontWeight="bold">
              {stats.totalRecipes}
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Total Recipes
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, gap: 1 }}>
              <Favorite sx={{ fontSize: 18, color: 'error.main' }} />
              <Typography variant="body2" color="text.secondary">
                {stats.favoriteRecipes} favorites
              </Typography>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              cursor: 'pointer',
              '&:hover': { bgcolor: 'action.hover' },
              transition: 'background-color 0.2s',
            }}
            onClick={() => navigate('/calendar')}
          >
            <CalendarMonth sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h3" fontWeight="bold">
              {upcomingMeals.length}
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Upcoming Meals
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Next 7 days
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              cursor: 'pointer',
              '&:hover': { bgcolor: 'action.hover' },
              transition: 'background-color 0.2s',
            }}
            onClick={() => navigate('/grocery-lists')}
          >
            <ShoppingCart sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h3" fontWeight="bold">
              {groceryLists.length}
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Active Lists
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Grocery lists
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Activity and Upcoming Meals */}
      <Grid container spacing={3}>
        {/* Recent Recipes */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Recently Added Recipes</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              {stats.recentRecipes.length === 0 ? (
                <Typography variant="body2" color="text.secondary" align="center" py={2}>
                  No recipes yet. Start by adding your first recipe!
                </Typography>
              ) : (
                <List>
                  {stats.recentRecipes.map((recipe) => (
                    <ListItem 
                      key={recipe.id}
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'action.hover' },
                        borderRadius: 1,
                      }}
                      onClick={() => navigate('/recipes')}
                    >
                      <ListItemIcon>
                        <Restaurant color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={recipe.title}
                        secondary={
                          <Box display="flex" gap={1} alignItems="center" mt={0.5}>
                            {recipe.prep_time && (
                              <Chip 
                                icon={<AccessTime />} 
                                label={`${recipe.prep_time} min`} 
                                size="small" 
                              />
                            )}
                            {recipe.is_favorite && (
                              <Favorite sx={{ fontSize: 16, color: 'error.main' }} />
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
              <Button 
                fullWidth 
                variant="outlined" 
                sx={{ mt: 2 }}
                onClick={() => navigate('/recipes')}
              >
                View All Recipes
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Upcoming Meals */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Event sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Upcoming Meals</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              {upcomingMeals.length === 0 ? (
                <Typography variant="body2" color="text.secondary" align="center" py={2}>
                  No meals planned. Start planning your week!
                </Typography>
              ) : (
                <List>
                  {upcomingMeals.map((meal) => (
                    <ListItem 
                      key={meal.id}
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'action.hover' },
                        borderRadius: 1,
                      }}
                      onClick={() => navigate('/calendar')}
                    >
                      <ListItemIcon>
                        <CalendarMonth color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={meal.recipe_name || 'Meal'}
                        secondary={
                          <Box display="flex" gap={1} alignItems="center" mt={0.5}>
                            <Chip 
                              label={formatMealDate(meal.meal_date)} 
                              size="small"
                              color={meal.meal_date && !isNaN(parseISO(meal.meal_date).getTime()) && isToday(parseISO(meal.meal_date)) ? 'primary' : 'default'}
                            />
                            <Chip 
                              label={meal.meal_type} 
                              size="small" 
                              variant="outlined"
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
              <Button 
                fullWidth 
                variant="outlined" 
                sx={{ mt: 2 }}
                onClick={() => navigate('/calendar')}
              >
                View Meal Calendar
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <OnboardingTutorial
        open={tutorialOpen}
        onClose={() => setTutorialOpen(false)}
      />
    </Box>
  )
}
