import { useState, useEffect, useCallback } from 'react'
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
  Chip,
  TablePagination,
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
import { calendarService, collectionService } from '../services'
import { useCalendarStore } from '../store/calendarStore'
import { useAuthStore } from '../store/authStore'
import RecipeSearchDialog from '../components/RecipeSearchDialog'
import CreateCalendarDialog from '../components/CreateCalendarDialog'
import { getErrorMessage } from '../utils/errorHandler'

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack']

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
    getLastActiveCalendarId,
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
  const [openCalendarSelector, setOpenCalendarSelector] = useState(false)
  const [selectedDate, setSelectedDate] = useState(null)
  const [selectedMealType, setSelectedMealType] = useState('dinner')
  
  // Calendar selector state
  const [calendarSearchTerm, setCalendarSearchTerm] = useState('')
  const [calendarSearchQuery, setCalendarSearchQuery] = useState('')
  const [calendarPage, setCalendarPage] = useState(0)
  const [calendarRowsPerPage, setCalendarRowsPerPage] = useState(10)
  const [availableCalendars, setAvailableCalendars] = useState([])
  const [loadingCalendars, setLoadingCalendars] = useState(false)
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
    collection_id: null,
  })
  const [prepopulateLoading, setPrepopulateLoading] = useState(false)
  const [collections, setCollections] = useState([])
  const [copyConfig, setCopyConfig] = useState({
    source_date: new Date().toISOString().split('T')[0],
    target_date: new Date().toISOString().split('T')[0],
    period: 'day',
    overwrite: false,
  })
  const [copyLoading, setCopyLoading] = useState(false)

  // Define loadAvailableCalendars with useCallback before it's used in useEffect
  const loadAvailableCalendars = useCallback(async () => {
    setLoadingCalendars(true)
    try {
      const params = {
        skip: calendarPage * calendarRowsPerPage,
        limit: calendarRowsPerPage,
      }
      if (calendarSearchQuery) {
        params.search = calendarSearchQuery
      }
      const data = await calendarService.getCalendars(params)
      setAvailableCalendars(data)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to load calendars'))
    } finally {
      setLoadingCalendars(false)
    }
  }, [calendarPage, calendarRowsPerPage, calendarSearchQuery, setError])

  useEffect(() => {
    loadCalendars()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (selectedCalendar) {
      loadMeals()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCalendar, currentWeekStart])

  useEffect(() => {
    if (openCalendarSelector) {
      loadAvailableCalendars()
    }
  }, [calendarPage, calendarRowsPerPage, calendarSearchQuery, openCalendarSelector, loadAvailableCalendars])

  useEffect(() => {
    if (openPrepopulate) {
      loadCollections()
    }
  }, [openPrepopulate, loadCollections])

  const loadCalendars = async () => {
    try {
      const data = await calendarService.getCalendars()
      setCalendars(data)
      
      // Try to restore last active calendar
      const lastCalendarId = getLastActiveCalendarId()
      if (lastCalendarId && data.length > 0) {
        const lastCalendar = data.find(c => c.id === lastCalendarId)
        if (lastCalendar) {
          setSelectedCalendar(lastCalendar)
          return
        }
      }
      
      // Fallback to first calendar if no last active or not found
      if (data.length > 0 && !selectedCalendar) {
        setSelectedCalendar(data[0])
      }
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to load calendars'))
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
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to load meals'))
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

  const handleCalendarCreated = (created) => {
    setCalendars([...calendars, created])
    setSelectedCalendar(created)
  }

  const handleAddMealClick = (date, mealType) => {
    setSelectedDate(date)
    setSelectedMealType(mealType)
    setOpenAddMeal(true)
  }

  const handleRecipeSelect = async (recipe) => {
    if (!recipe || !selectedCalendar || !selectedDate) return

    try {
      // Set time to noon to avoid timezone issues
      const mealDateTime = new Date(selectedDate)
      mealDateTime.setHours(12, 0, 0, 0)
      
      const mealData = {
        recipe_id: recipe.id,
        meal_date: mealDateTime.toISOString(),
        meal_type: selectedMealType,
      }
      const newMeal = await calendarService.addMealToCalendar(
        selectedCalendar.id,
        mealData
      )
      addMeal(newMeal)
      setOpenAddMeal(false)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to add meal'))
    }
  }

  const handleDeleteMeal = async (mealId) => {
    if (!selectedCalendar) return
    
    try {
      await calendarService.removeMealFromCalendar(selectedCalendar.id, mealId)
      removeMeal(mealId)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to delete meal'))
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
        collection_id: prepopulateConfig.collection_id,
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
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to prepopulate calendar'))
    } finally {
      setPrepopulateLoading(false)
    }
  }

  const loadCollections = useCallback(async () => {
    try {
      const data = await collectionService.getCollections()
      setCollections(data)
    } catch (err) {
      console.error('Failed to load collections:', err)
    }
  }, [])

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
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to copy calendar period'))
    } finally {
      setCopyLoading(false)
    }
  }

  const handleOpenCalendarSelector = async () => {
    setOpenCalendarSelector(true)
    await loadAvailableCalendars()
  }

  const handleCalendarSearch = () => {
    setCalendarSearchQuery(calendarSearchTerm)
    setCalendarPage(0)
  }

  const handleCalendarSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleCalendarSearch()
    }
  }

  const handleSelectCalendar = (calendar) => {
    setSelectedCalendar(calendar)
    setOpenCalendarSelector(false)
    setCalendarSearchTerm('')
    setCalendarSearchQuery('')
    setCalendarPage(0)
  }

  const getMealsForDateAndType = (date, mealType) => {
    return meals.filter(
      (meal) =>
        isSameDay(parseISO(meal.meal_date), date) && meal.meal_type === mealType
    )
  }

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
        <CreateCalendarDialog
          open={openCreateCalendar}
          onClose={() => setOpenCreateCalendar(false)}
          onCalendarCreated={handleCalendarCreated}
        />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" gap={2} mb={3} flexWrap="wrap">
        <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
          <Typography variant="h4" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>{selectedCalendar?.name || 'Meal Calendar'}</Typography>
          <Button
            variant="outlined"
            size="small"
            onClick={handleOpenCalendarSelector}
          >
            Switch
          </Button>
          <Button
            variant="outlined"
            size="small"
            startIcon={<AddIcon />}
            onClick={() => setOpenCreateCalendar(true)}
          >
            New
          </Button>
        </Box>
        <Box display="flex" gap={1} alignItems="center" flexWrap="wrap">
          <Button
            variant="contained"
            size="small"
            startIcon={<AutoAwesomeIcon />}
            onClick={() => setOpenPrepopulate(true)}
            color="secondary"
            disabled={!selectedCalendar?.can_edit}
          >
            Prepopulate
          </Button>
          <Button
            variant="outlined"
            size="small"
            startIcon={<ContentCopyIcon />}
            onClick={() => setOpenCopy(true)}
            disabled={!selectedCalendar?.can_edit}
          >
            Copy
          </Button>
        </Box>
      </Box>

      <Box display="flex" gap={1} alignItems="center" justifyContent="center" mb={3}>
        <IconButton onClick={handlePreviousWeek} size="small">
          <ChevronLeft />
        </IconButton>
        <Typography variant="subtitle1" sx={{ minWidth: '200px', textAlign: 'center', fontSize: { xs: '0.875rem', sm: '1rem' } }}>
          {format(currentWeekStart, 'MMM d')} -{' '}
          {format(addDays(currentWeekStart, 6), 'MMM d, yyyy')}
        </Typography>
        <IconButton onClick={handleNextWeek} size="small">
          <ChevronRight />
        </IconButton>
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
        <Box sx={{ mb: 3 }}>
          {/* Mobile View - Card per Day */}
          <Box sx={{ display: { xs: 'block', md: 'none' } }}>
            {Array.from({ length: 7 }, (_, i) => addDays(currentWeekStart, i)).map((day) => (
              <Card key={day.toISOString()} sx={{ mb: 2 }}>
                <CardContent>
                  <Box sx={{ mb: 2, pb: 1, borderBottom: '1px solid #eee' }}>
                    <Typography variant="h6" fontWeight="bold">
                      {format(day, 'EEEE')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {format(day, 'MMMM d, yyyy')}
                    </Typography>
                  </Box>

                  {MEAL_TYPES.map((mealType) => {
                    const dayMeals = getMealsForDateAndType(day, mealType)
                    return (
                      <Box key={mealType} sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="subtitle2" fontWeight="bold" textTransform="capitalize">
                            {mealType}
                          </Typography>
                          {selectedCalendar?.can_edit && (
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<AddIcon />}
                              onClick={() => handleAddMealClick(day, mealType)}
                              sx={{ minWidth: 'auto', px: 1 }}
                            >
                              Add
                            </Button>
                          )}
                        </Box>

                        {dayMeals.length > 0 ? (
                          <Box sx={{ ml: 1, mb: 1 }}>
                            {dayMeals.map((meal) => (
                              <Box
                                key={meal.id}
                                sx={{
                                  p: 1,
                                  mb: 1,
                                  bgcolor: 'action.hover',
                                  borderRadius: 1,
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                }}
                              >
                                <Typography variant="body2" noWrap sx={{ flex: 1 }}>
                                  {meal.recipe_name || 'Unknown Recipe'}
                                </Typography>
                                {selectedCalendar?.can_edit && (
                                  <IconButton
                                    size="small"
                                    onClick={() => handleDeleteMeal(meal.id)}
                                    sx={{ ml: 1 }}
                                  >
                                    <DeleteIcon fontSize="small" />
                                  </IconButton>
                                )}
                              </Box>
                            ))}
                          </Box>
                        ) : (
                          <Typography variant="caption" color="text.secondary" sx={{ ml: 1, display: 'block' }}>
                            No meals planned
                          </Typography>
                        )}
                      </Box>
                    )
                  })}
                </CardContent>
              </Card>
            ))}
          </Box>

          {/* Desktop View - Table Layout */}
          <Box sx={{ display: { xs: 'none', md: 'block' }, overflowX: 'auto' }}>
            <Grid container spacing={1} sx={{ minWidth: { sm: 1200 } }}>
              <Grid item xs={12} sm={1.5}>
                <Paper sx={{ p: { xs: 0.5, sm: 1 }, minHeight: { xs: 60, sm: 100 } }}>
                  <Typography variant="subtitle2" fontWeight="bold" sx={{ fontSize: { xs: '0.75rem', sm: 'inherit' } }}>
                    Meal Type
                  </Typography>
                </Paper>
              </Grid>
              {Array.from({ length: 7 }, (_, i) => addDays(currentWeekStart, i)).map((day) => (
                <Grid item xs={12} sm={1.5} key={day.toISOString()}>
                  <Paper sx={{ p: { xs: 0.5, sm: 1 }, textAlign: 'center', minHeight: { xs: 60, sm: 100 } }}>
                    <Typography variant="subtitle2" fontWeight="bold" sx={{ fontSize: { xs: '0.75rem', sm: 'inherit' } }}>
                      {format(day, 'EEE')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.65rem', sm: 'inherit' } }}>
                      {format(day, 'MMM d')}
                    </Typography>
                  </Paper>
                </Grid>
              ))}

              {MEAL_TYPES.map((mealType) => (
                <Grid container item spacing={1} key={mealType}>
                  <Grid item xs={12} sm={1.5}>
                    <Paper sx={{ p: { xs: 1, sm: 2 }, minHeight: { xs: 100, sm: 150 } }}>
                      <Typography
                        variant="subtitle2"
                        fontWeight="bold"
                        textTransform="capitalize"
                        sx={{ fontSize: { xs: '0.75rem', sm: 'inherit' } }}
                      >
                        {mealType}
                      </Typography>
                    </Paper>
                  </Grid>
                  {Array.from({ length: 7 }, (_, i) => addDays(currentWeekStart, i)).map((day) => {
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
                              cursor: selectedCalendar?.can_edit ? 'pointer' : 'default',
                              '&:hover': selectedCalendar?.can_edit ? { bgcolor: 'action.hover' } : {},
                              borderRadius: 1,
                              p: 0.5,
                              minHeight: dayMeals.length === 0 ? 100 : 'auto',
                            }}
                            onClick={() => selectedCalendar?.can_edit && handleAddMealClick(day, mealType)}
                          >
                            {dayMeals.map((meal) => {
                              return (
                                <Card key={meal.id} sx={{ mb: 1, position: 'relative' }}>
                                  <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                                    <Typography variant="caption" noWrap>
                                      {meal.recipe_name || 'Unknown Recipe'}
                                    </Typography>
                                    {selectedCalendar?.can_edit && (
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
                                    )}
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
      <CreateCalendarDialog
        open={openCreateCalendar}
        onClose={() => setOpenCreateCalendar(false)}
        onCalendarCreated={handleCalendarCreated}
      />

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

          <FormControl fullWidth margin="normal">
            <InputLabel>Recipe Collection (Optional)</InputLabel>
            <Select
              value={prepopulateConfig.collection_id || ''}
              label="Recipe Collection (Optional)"
              onChange={(e) => setPrepopulateConfig({ ...prepopulateConfig, collection_id: e.target.value || null })}
            >
              <MenuItem value="">Any Collection</MenuItem>
              {collections.map((collection) => (
                <MenuItem key={collection.id} value={collection.id}>
                  {collection.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

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
            label="Avoid duplicate menu items"
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

      {/* Calendar Selector Dialog */}
      <Dialog open={openCalendarSelector} onClose={() => setOpenCalendarSelector(false)} maxWidth="md" fullWidth>
        <DialogTitle>Select Calendar</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2, mt: 1, display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              placeholder="Search calendars..."
              value={calendarSearchTerm}
              onChange={(e) => setCalendarSearchTerm(e.target.value)}
              onKeyPress={handleCalendarSearchKeyPress}
            />
            <Button variant="contained" onClick={handleCalendarSearch}>
              Search
            </Button>
          </Box>

          {loadingCalendars ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : availableCalendars.length === 0 ? (
            <Alert severity="info">No calendars found</Alert>
          ) : (
            <Box>
              {availableCalendars.map((cal) => (
                <Paper
                  key={cal.id}
                  sx={{
                    p: 2,
                    mb: 1,
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'action.hover' },
                    bgcolor: selectedCalendar?.id === cal.id ? 'action.selected' : 'transparent',
                  }}
                  onClick={() => handleSelectCalendar(cal)}
                >
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        {cal.name}
                      </Typography>
                      <Box display="flex" gap={1} mt={0.5}>
                        <Chip
                          label={cal.visibility}
                          size="small"
                          color={cal.visibility === 'public' ? 'success' : cal.visibility === 'group' ? 'primary' : 'default'}
                        />
                        {!cal.can_edit && (
                          <Chip label="Read Only" size="small" variant="outlined" />
                        )}
                      </Box>
                    </Box>
                    {selectedCalendar?.id === cal.id && (
                      <Chip label="Current" color="primary" size="small" />
                    )}
                  </Box>
                </Paper>
              ))}
              {availableCalendars.length > 0 && availableCalendars.length >= calendarRowsPerPage && (
                <TablePagination
                  component="div"
                  count={-1}
                  page={calendarPage}
                  onPageChange={(e, newPage) => setCalendarPage(newPage)}
                  rowsPerPage={calendarRowsPerPage}
                  onRowsPerPageChange={(e) => {
                    setCalendarRowsPerPage(parseInt(e.target.value, 10))
                    setCalendarPage(0)
                  }}
                  rowsPerPageOptions={[5, 10, 25]}
                />
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCalendarSelector(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

