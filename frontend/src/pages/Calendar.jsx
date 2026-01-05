import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Button,
  Grid,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  Checkbox,
  FormControlLabel,
  FormGroup,
  FormLabel,
} from '@mui/material'
import {
  ChevronLeft,
  ChevronRight,
  Add as AddIcon,
  Delete as DeleteIcon,
  AutoAwesome as AutoAwesomeIcon,
  ContentCopy as ContentCopyIcon,
} from '@mui/icons-material'
import { format, startOfWeek, addDays, isSameDay, parseISO } from 'date-fns'
import { calendarService, groupService } from '../services'
import { useCalendarStore } from '../store/calendarStore'
import { useAuthStore } from '../store/authStore'
import RecipeSearchDialog from '../components/RecipeSearchDialog'

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack']
const VISIBILITY_OPTIONS = [
  { value: 'private', label: 'Private (Only me)' },
  { value: 'group', label: 'Group (Shared with group)' },
  { value: 'public', label: 'Public (Everyone)' },
]

export default function Calendar() {
  const { user } = useAuthStore()
  const {
    calendars,
    setCalendars,
    selectedCalendar,
    setSelectedCalendar,
    meals,
    setMeals,
    addMeal,
    removeMeal,
    loading,
    setLoading,
    error,
    setError,
    clearError,
  } = useCalendarStore()

  // Get week start day from user preferences, default to Sunday (0)
  const weekStartDay = user?.preferences?.calendar_start_day === 'monday' ? 1 :
    user?.preferences?.calendar_start_day === 'saturday' ? 6 : 0

  const [currentWeekStart, setCurrentWeekStart] = useState(() =>
    startOfWeek(new Date(), { weekStartsOn: weekStartDay })
  )
  const [openAddMeal, setOpenAddMeal] = useState(false)
  const [openCreateCalendar, setOpenCreateCalendar] = useState(false)
  const [openPrepopulate, setOpenPrepopulate] = useState(false)
  const [openCopy, setOpenCopy] = useState(false)
  const [selectedDate, setSelectedDate] = useState(null)
  const [selectedMealType, setSelectedMealType] = useState('dinner')
  const [groups, setGroups] = useState([])
  const [newCalendar, setNewCalendar] = useState({
    name: '',
    visibility: 'private',
    group_id: null,
  })
  const [prepopulateConfig, setPrepopulateConfig] = useState({
    start_date: new Date().toISOString().split('T')[0],
    period: 'week',
    meal_types: {
      breakfast: true,
      lunch: true,
      dinner: true,
    },
    snacks_per_day: 0,
    desserts_per_day: 0,
    use_dietary_preferences: true,
    avoid_duplicates: true,
  })
  const [prepopulateLoading, setPrepopulateLoading] = useState(false)
  const [copyConfig, setCopyConfig] = useState({
    source_date: new Date().toISOString().split('T')[0],
    target_date: new Date().toISOString().split('T')[0],
    period: 'day',
    overwrite: false,
  })
  const [copyLoading, setCopyLoading] = useState(false)

  useEffect(() => {
    loadCalendars()
    loadGroups()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (selectedCalendar) {
      loadMeals()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCalendar, currentWeekStart])

  const loadCalendars = async () => {
    try {
      const data = await calendarService.getCalendars()
      setCalendars(data)
      if (data.length > 0 && !selectedCalendar) {
        setSelectedCalendar(data[0])
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load calendars')
    }
  }

  const loadGroups = async () => {
    try {
      const data = await groupService.getGroups()
      setGroups(data)
    } catch (err) {
      console.error('Failed to load groups:', err)
    }
  }

  const loadMeals = async () => {
    if (!selectedCalendar) return
    
    setLoading(true)
    clearError()
    try {
      const endDate = addDays(currentWeekStart, 6)
      const data = await calendarService.getCalendarMeals(selectedCalendar.id, {
        start_date: currentWeekStart.toISOString(),
        end_date: endDate.toISOString(),
      })
      setMeals(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load meals')
    } finally {
      setLoading(false)
    }
  }

  const handlePreviousWeek = () => {
    setCurrentWeekStart(addDays(currentWeekStart, -7))
  }

  const handleNextWeek = () => {
    setCurrentWeekStart(addDays(currentWeekStart, 7))
  }

  const handleCreateCalendar = async () => {
    if (!newCalendar.name.trim()) {
      setError('Calendar name is required')
      return
    }

    try {
      const calendarData = {
        name: newCalendar.name,
        visibility: newCalendar.visibility,
        ...(newCalendar.visibility === 'group' && newCalendar.group_id && { group_id: parseInt(newCalendar.group_id) }),
      }
      const created = await calendarService.createCalendar(calendarData)
      setCalendars([...calendars, created])
      setSelectedCalendar(created)
      setOpenCreateCalendar(false)
      setNewCalendar({ name: '', visibility: 'private', group_id: null })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create calendar')
    }
  }

  const handleAddMealClick = (date, mealType) => {
    setSelectedDate(date)
    setSelectedMealType(mealType)
    setOpenAddMeal(true)
  }

  const handleRecipeSelect = async (recipe) => {
    if (!recipe || !selectedCalendar) return

    try {
      const mealData = {
        recipe_id: recipe.id,
        meal_type: selectedMealType,
      }
      const newMeal = await calendarService.addMealToCalendar(
        selectedCalendar.id,
        mealData
      )
      addMeal(newMeal)
      setOpenAddMeal(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add meal')
    }
  }

  const handleDeleteMeal = async (mealId) => {
    if (!selectedCalendar) return
    
    try {
      await calendarService.removeMealFromCalendar(selectedCalendar.id, mealId)
      removeMeal(mealId)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete meal')
    }
  }

  const handlePrepopulate = async () => {
    if (!selectedCalendar) return

    setPrepopulateLoading(true)
    clearError()
    
    try {
      // Get selected meal types as array
      const selectedMealTypes = Object.keys(prepopulateConfig.meal_types).filter(
        (key) => prepopulateConfig.meal_types[key]
      )

      if (selectedMealTypes.length === 0) {
        setError('Please select at least one meal type')
        setPrepopulateLoading(false)
        return
      }

      // Create ISO datetime for start_date
      const startDate = new Date(prepopulateConfig.start_date)
      startDate.setHours(12, 0, 0, 0) // Set to noon to avoid timezone issues

      const requestData = {
        start_date: startDate.toISOString(),
        period: prepopulateConfig.period,
        meal_types: selectedMealTypes,
        snacks_per_day: parseInt(prepopulateConfig.snacks_per_day) || 0,
        desserts_per_day: parseInt(prepopulateConfig.desserts_per_day) || 0,
        use_dietary_preferences: prepopulateConfig.use_dietary_preferences,
        avoid_duplicates: prepopulateConfig.avoid_duplicates,
      }

      await calendarService.prepopulateCalendar(
        selectedCalendar.id,
        requestData
      )

      // Reload meals to show the new ones
      await loadMeals()
      
      setOpenPrepopulate(false)
      
      // Show success message
      setError(null)
      // Could add a success state/snackbar here
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to prepopulate calendar')
    } finally {
      setPrepopulateLoading(false)
    }
  }

  const handleCopy = async () => {
    if (!selectedCalendar) return

    setCopyLoading(true)
    clearError()
    
    try {
      // Create ISO datetime for dates
      const sourceDate = new Date(copyConfig.source_date)
      sourceDate.setHours(12, 0, 0, 0) // Set to noon to avoid timezone issues

      const targetDate = new Date(copyConfig.target_date)
      targetDate.setHours(12, 0, 0, 0) // Set to noon to avoid timezone issues

      const requestData = {
        source_date: sourceDate.toISOString(),
        target_date: targetDate.toISOString(),
        period: copyConfig.period,
        overwrite: copyConfig.overwrite,
      }

      await calendarService.copyCalendarPeriod(
        selectedCalendar.id,
        requestData
      )

      // Reload meals to show the copied ones
      await loadMeals()
      
      setOpenCopy(false)
      
      // Show success message
      setError(null)
      // Could add a success state/snackbar here
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to copy calendar period')
    } finally {
      setCopyLoading(false)
    }
  }

  const getMealsForDateAndType = (date, mealType) => {
    return meals.filter(
      (meal) =>
        isSameDay(parseISO(meal.meal_date), date) && meal.meal_type === mealType
    )
  }

  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(currentWeekStart, i))

  if (!selectedCalendar) {
    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">
            Meal Calendar
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenCreateCalendar(true)}
          >
            Create Calendar
          </Button>
        </Box>
        <Alert severity="info">
          No calendar found. Create a calendar to start planning meals.
        </Alert>

        {/* Create Calendar Dialog */}
        <Dialog open={openCreateCalendar} onClose={() => setOpenCreateCalendar(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Create New Calendar</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              fullWidth
              label="Calendar Name"
              value={newCalendar.name}
              onChange={(e) => setNewCalendar({ ...newCalendar, name: e.target.value })}
              margin="normal"
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Visibility</InputLabel>
              <Select
                value={newCalendar.visibility}
                label="Visibility"
                onChange={(e) => setNewCalendar({ ...newCalendar, visibility: e.target.value, group_id: null })}
              >
                {VISIBILITY_OPTIONS.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {newCalendar.visibility === 'group' && (
              <FormControl fullWidth margin="normal">
                <InputLabel>Group</InputLabel>
                <Select
                  value={newCalendar.group_id || ''}
                  label="Group"
                  onChange={(e) => setNewCalendar({ ...newCalendar, group_id: e.target.value })}
                >
                  <MenuItem value="">
                    <em>Select a group</em>
                  </MenuItem>
                  {groups.map((group) => (
                    <MenuItem key={group.id} value={group.id}>
                      {group.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenCreateCalendar(false)}>Cancel</Button>
            <Button onClick={handleCreateCalendar} variant="contained">
              Create
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h4">Meal Calendar</Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={<AddIcon />}
            onClick={() => setOpenCreateCalendar(true)}
          >
            New Calendar
          </Button>
          <Button
            variant="contained"
            size="small"
            startIcon={<AutoAwesomeIcon />}
            onClick={() => setOpenPrepopulate(true)}
            color="secondary"
          >
            Prepopulate
          </Button>
          <Button
            variant="outlined"
            size="small"
            startIcon={<ContentCopyIcon />}
            onClick={() => setOpenCopy(true)}
          >
            Copy
          </Button>
        </Box>
        <Box display="flex" gap={2} alignItems="center">
          <IconButton onClick={handlePreviousWeek}>
            <ChevronLeft />
          </IconButton>
          <Typography variant="h6">
            {format(currentWeekStart, 'MMM d')} -{' '}
            {format(addDays(currentWeekStart, 6), 'MMM d, yyyy')}
          </Typography>
          <IconButton onClick={handleNextWeek}>
            <ChevronRight />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" onClose={clearError} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : (
        <Box sx={{ overflowX: 'auto' }}>
          <Grid container spacing={1} sx={{ minWidth: 1000 }}>
            <Grid item xs={1.5}>
              <Paper sx={{ p: 1, minHeight: 100 }}>
                <Typography variant="subtitle2" fontWeight="bold">
                  Meal Type
                </Typography>
              </Paper>
            </Grid>
            {weekDays.map((day) => (
              <Grid item xs={1.5} key={day.toISOString()}>
                <Paper sx={{ p: 1, textAlign: 'center', minHeight: 100 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    {format(day, 'EEE')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {format(day, 'MMM d')}
                  </Typography>
                </Paper>
              </Grid>
            ))}

            {MEAL_TYPES.map((mealType) => (
              <Grid container item spacing={1} key={mealType}>
                <Grid item xs={1.5}>
                  <Paper sx={{ p: 2, minHeight: 150 }}>
                    <Typography
                      variant="subtitle2"
                      fontWeight="bold"
                      textTransform="capitalize"
                    >
                      {mealType}
                    </Typography>
                  </Paper>
                </Grid>
                {weekDays.map((day) => {
                  const dayMeals = getMealsForDateAndType(day, mealType)
                  return (
                    <Grid item xs={1.5} key={`${day.toISOString()}-${mealType}`}>
                      <Paper
                        sx={{
                          p: 1,
                          minHeight: 150,
                          bgcolor: 'background.default',
                          position: 'relative',
                        }}
                      >
                        <Box
                          sx={{
                            cursor: 'pointer',
                            '&:hover': { bgcolor: 'action.hover' },
                            borderRadius: 1,
                            p: 0.5,
                            minHeight: dayMeals.length === 0 ? 100 : 'auto',
                          }}
                          onClick={() => handleAddMealClick(day, mealType)}
                        >
                          {dayMeals.map((meal) => {
                            return (
                              <Card key={meal.id} sx={{ mb: 1, position: 'relative' }}>
                                <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                                  <Typography variant="caption" noWrap>
                                    {meal.recipe_name || 'Unknown Recipe'}
                                  </Typography>
                                  <IconButton
                                    size="small"
                                    sx={{ position: 'absolute', top: 0, right: 0 }}
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      handleDeleteMeal(meal.id)
                                    }}
                                  >
                                    <DeleteIcon fontSize="small" />
                                  </IconButton>
                                </CardContent>
                              </Card>
                            )
                          })}
                          {dayMeals.length === 0 ? (
                            <Box
                              display="flex"
                              alignItems="center"
                              justifyContent="center"
                              minHeight={100}
                            >
                              <AddIcon color="action" />
                            </Box>
                          ) : (
                            <Box
                              display="flex"
                              alignItems="center"
                              justifyContent="center"
                              sx={{ mt: 0.5 }}
                            >
                              <IconButton
                                size="small"
                                color="primary"
                                sx={{
                                  bgcolor: 'action.hover',
                                  '&:hover': { bgcolor: 'action.selected' },
                                }}
                              >
                                <AddIcon fontSize="small" />
                              </IconButton>
                            </Box>
                          )}
                        </Box>
                      </Paper>
                    </Grid>
                  )
                })}
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Recipe Search Dialog for Adding Meals */}
      <RecipeSearchDialog
        open={openAddMeal}
        onClose={() => setOpenAddMeal(false)}
        onSelect={handleRecipeSelect}
        title={`Add Meal - ${selectedDate ? format(selectedDate, 'EEEE, MMM d') : ''} (${selectedMealType})`}
      />

      {/* Create Calendar Dialog */}
      <Dialog open={openCreateCalendar} onClose={() => setOpenCreateCalendar(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Calendar</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Calendar Name"
            value={newCalendar.name}
            onChange={(e) => setNewCalendar({ ...newCalendar, name: e.target.value })}
            margin="normal"
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Visibility</InputLabel>
            <Select
              value={newCalendar.visibility}
              label="Visibility"
              onChange={(e) => setNewCalendar({ ...newCalendar, visibility: e.target.value, group_id: null })}
            >
              {VISIBILITY_OPTIONS.map((opt) => (
                <MenuItem key={opt.value} value={opt.value}>
                  {opt.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {newCalendar.visibility === 'group' && (
            <FormControl fullWidth margin="normal">
              <InputLabel>Group</InputLabel>
              <Select
                value={newCalendar.group_id || ''}
                label="Group"
                onChange={(e) => setNewCalendar({ ...newCalendar, group_id: e.target.value })}
              >
                <MenuItem value="">
                  <em>Select a group</em>
                </MenuItem>
                {groups.map((group) => (
                  <MenuItem key={group.id} value={group.id}>
                    {group.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateCalendar(false)}>Cancel</Button>
          <Button onClick={handleCreateCalendar} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Prepopulate Calendar Dialog */}
      <Dialog open={openPrepopulate} onClose={() => setOpenPrepopulate(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Prepopulate Calendar</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Start Date"
            type="date"
            value={prepopulateConfig.start_date}
            onChange={(e) => setPrepopulateConfig({ ...prepopulateConfig, start_date: e.target.value })}
            margin="normal"
            InputLabelProps={{ shrink: true }}
          />
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Time Period</InputLabel>
            <Select
              value={prepopulateConfig.period}
              label="Time Period"
              onChange={(e) => setPrepopulateConfig({ ...prepopulateConfig, period: e.target.value })}
            >
              <MenuItem value="day">Day</MenuItem>
              <MenuItem value="week">Week</MenuItem>
              <MenuItem value="month">Month</MenuItem>
            </Select>
          </FormControl>

          <FormControl component="fieldset" margin="normal" fullWidth>
            <FormLabel component="legend">Meal Types</FormLabel>
            <FormGroup>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={prepopulateConfig.meal_types.breakfast}
                    onChange={(e) =>
                      setPrepopulateConfig({
                        ...prepopulateConfig,
                        meal_types: { ...prepopulateConfig.meal_types, breakfast: e.target.checked },
                      })
                    }
                  />
                }
                label="Breakfast"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={prepopulateConfig.meal_types.lunch}
                    onChange={(e) =>
                      setPrepopulateConfig({
                        ...prepopulateConfig,
                        meal_types: { ...prepopulateConfig.meal_types, lunch: e.target.checked },
                      })
                    }
                  />
                }
                label="Lunch"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={prepopulateConfig.meal_types.dinner}
                    onChange={(e) =>
                      setPrepopulateConfig({
                        ...prepopulateConfig,
                        meal_types: { ...prepopulateConfig.meal_types, dinner: e.target.checked },
                      })
                    }
                  />
                }
                label="Dinner"
              />
            </FormGroup>
          </FormControl>

          <TextField
            fullWidth
            label="Snacks per Day"
            type="number"
            value={prepopulateConfig.snacks_per_day}
            onChange={(e) => setPrepopulateConfig({ ...prepopulateConfig, snacks_per_day: e.target.value })}
            margin="normal"
            inputProps={{ min: 0, max: 5 }}
          />

          <TextField
            fullWidth
            label="Desserts per Day"
            type="number"
            value={prepopulateConfig.desserts_per_day}
            onChange={(e) => setPrepopulateConfig({ ...prepopulateConfig, desserts_per_day: e.target.value })}
            margin="normal"
            inputProps={{ min: 0, max: 3 }}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={prepopulateConfig.use_dietary_preferences}
                onChange={(e) =>
                  setPrepopulateConfig({
                    ...prepopulateConfig,
                    use_dietary_preferences: e.target.checked,
                  })
                }
              />
            }
            label="Use my dietary preferences"
            sx={{ mt: 2 }}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={prepopulateConfig.avoid_duplicates}
                onChange={(e) =>
                  setPrepopulateConfig({
                    ...prepopulateConfig,
                    avoid_duplicates: e.target.checked,
                  })
                }
              />
            }
            label="Avoid duplicate recipes"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPrepopulate(false)} disabled={prepopulateLoading}>
            Cancel
          </Button>
          <Button onClick={handlePrepopulate} variant="contained" disabled={prepopulateLoading}>
            {prepopulateLoading ? <CircularProgress size={24} /> : 'Prepopulate'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Copy Calendar Dialog */}
      <Dialog open={openCopy} onClose={() => setOpenCopy(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Copy Calendar Period</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>Period to Copy</InputLabel>
            <Select
              value={copyConfig.period}
              label="Period to Copy"
              onChange={(e) => setCopyConfig({ ...copyConfig, period: e.target.value })}
            >
              <MenuItem value="day">Day</MenuItem>
              <MenuItem value="week">Week</MenuItem>
              <MenuItem value="month">Month</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Source Date (Copy From)"
            type="date"
            value={copyConfig.source_date}
            onChange={(e) => setCopyConfig({ ...copyConfig, source_date: e.target.value })}
            margin="normal"
            InputLabelProps={{ shrink: true }}
            helperText={`Copy meals from this ${copyConfig.period}`}
          />
          
          <TextField
            fullWidth
            label="Target Date (Copy To)"
            type="date"
            value={copyConfig.target_date}
            onChange={(e) => setCopyConfig({ ...copyConfig, target_date: e.target.value })}
            margin="normal"
            InputLabelProps={{ shrink: true }}
            helperText={`Paste meals to this ${copyConfig.period}`}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={copyConfig.overwrite}
                onChange={(e) =>
                  setCopyConfig({
                    ...copyConfig,
                    overwrite: e.target.checked,
                  })
                }
              />
            }
            label="Overwrite existing meals"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCopy(false)} disabled={copyLoading}>
            Cancel
          </Button>
          <Button onClick={handleCopy} variant="contained" disabled={copyLoading}>
            {copyLoading ? <CircularProgress size={24} /> : 'Copy'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

