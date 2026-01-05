import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Autocomplete,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  CircularProgress,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
} from '@mui/material'
import {
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material'
import { recipeService } from '../services'

const DIFFICULTIES = ['easy', 'medium', 'hard']
const CATEGORIES = ['breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'staple', 'frozen']

export default function RecipeSearchDialog({ open, onClose, onSelect, title = "Search Recipes" }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [recipes, setRecipes] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedRecipe, setSelectedRecipe] = useState(null)
  
  // Filters
  const [selectedCategory, setSelectedCategory] = useState('')
  const [selectedDifficulty, setSelectedDifficulty] = useState('')
  const [selectedTags, setSelectedTags] = useState([])
  const [maxPrepTime, setMaxPrepTime] = useState('')
  const [maxCookTime, setMaxCookTime] = useState('')
  
  // Available tags
  const [allTagsList, setAllTagsList] = useState([])

  useEffect(() => {
    if (open) {
      loadTags()
      handleSearch()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const loadTags = async () => {
    try {
      const tags = await recipeService.getAllTags()
      
      // Flatten tags for autocomplete
      const tagsList = []
      Object.keys(tags).forEach(category => {
        tags[category].forEach(tag => {
          tagsList.push({ name: tag.name, category, count: tag.count })
        })
      })
      setAllTagsList(tagsList)
    } catch (err) {
      console.error('Failed to load tags:', err)
    }
  }

  const handleSearch = async () => {
    setLoading(true)
    try {
      const params = {}
      
      if (searchTerm) {
        params.search = searchTerm
      }
      
      if (selectedCategory) {
        params.category = selectedCategory
      }
      
      if (selectedDifficulty) {
        params.difficulty = selectedDifficulty
      }
      
      if (selectedTags.length > 0) {
        params.tags = selectedTags.join(',')
      }
      
      if (maxPrepTime) {
        params.max_prep_time = parseInt(maxPrepTime)
      }
      
      if (maxCookTime) {
        params.max_cook_time = parseInt(maxCookTime)
      }
      
      const data = await recipeService.getRecipes(params)
      setRecipes(data)
    } catch (err) {
      console.error('Failed to search recipes:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleClearFilters = () => {
    setSearchTerm('')
    setSelectedCategory('')
    setSelectedDifficulty('')
    setSelectedTags([])
    setMaxPrepTime('')
    setMaxCookTime('')
  }

  const handleSelectRecipe = () => {
    if (selectedRecipe && onSelect) {
      onSelect(selectedRecipe)
      handleClose()
    }
  }

  const handleClose = () => {
    setSelectedRecipe(null)
    setSearchTerm('')
    setRecipes([])
    onClose()
  }

  const hasActiveFilters = selectedCategory || selectedDifficulty || selectedTags.length > 0 || maxPrepTime || maxCookTime

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 1 }}>
          {/* Search Input */}
          <TextField
            fullWidth
            placeholder="Search by recipe name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSearch()
              }
            }}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
            sx={{ mb: 2 }}
          />

          {/* Advanced Filters */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center" gap={1}>
                <FilterIcon />
                <Typography>
                  Advanced Filters
                  {hasActiveFilters && (
                    <Chip 
                      label="Active" 
                      size="small" 
                      color="primary" 
                      sx={{ ml: 1 }} 
                    />
                  )}
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {/* Category Filter */}
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={selectedCategory}
                      label="Category"
                      onChange={(e) => setSelectedCategory(e.target.value)}
                    >
                      <MenuItem value="">
                        <em>All Categories</em>
                      </MenuItem>
                      {CATEGORIES.map((cat) => (
                        <MenuItem key={cat} value={cat}>
                          {cat.charAt(0).toUpperCase() + cat.slice(1)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                {/* Difficulty Filter */}
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Difficulty</InputLabel>
                    <Select
                      value={selectedDifficulty}
                      label="Difficulty"
                      onChange={(e) => setSelectedDifficulty(e.target.value)}
                    >
                      <MenuItem value="">
                        <em>All Difficulties</em>
                      </MenuItem>
                      {DIFFICULTIES.map((diff) => (
                        <MenuItem key={diff} value={diff}>
                          {diff.charAt(0).toUpperCase() + diff.slice(1)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                {/* Tags Filter */}
                <Grid item xs={12}>
                  <Autocomplete
                    multiple
                    options={allTagsList}
                    getOptionLabel={(option) => option.name}
                    groupBy={(option) => option.category}
                    value={allTagsList.filter(tag => selectedTags.includes(tag.name))}
                    onChange={(event, newValue) => {
                      setSelectedTags(newValue.map(tag => tag.name))
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Tags"
                        placeholder="Select tags..."
                      />
                    )}
                    renderTags={(value, getTagProps) =>
                      value.map((option, index) => (
                        <Chip
                          key={option.name}
                          label={option.name}
                          {...getTagProps({ index })}
                          size="small"
                        />
                      ))
                    }
                  />
                </Grid>

                {/* Time Filters */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Max Prep Time (minutes)"
                    value={maxPrepTime}
                    onChange={(e) => setMaxPrepTime(e.target.value)}
                    inputProps={{ min: 0 }}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Max Cook Time (minutes)"
                    value={maxCookTime}
                    onChange={(e) => setMaxCookTime(e.target.value)}
                    inputProps={{ min: 0 }}
                  />
                </Grid>

                {/* Clear Filters Button */}
                <Grid item xs={12}>
                  <Box display="flex" justifyContent="space-between">
                    <Button 
                      onClick={handleClearFilters} 
                      disabled={!hasActiveFilters}
                    >
                      Clear All Filters
                    </Button>
                    <Button 
                      variant="contained" 
                      onClick={handleSearch}
                      startIcon={<SearchIcon />}
                    >
                      Search
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>

          {/* Results */}
          <Box sx={{ mt: 2 }}>
            {loading ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : recipes.length === 0 ? (
              <Typography color="text.secondary" align="center" sx={{ py: 3 }}>
                {searchTerm || hasActiveFilters ? 'No recipes found. Try adjusting your search.' : 'Start searching to see recipes.'}
              </Typography>
            ) : (
              <>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  {recipes.length} recipe{recipes.length !== 1 ? 's' : ''} found
                </Typography>
                <List sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {recipes.map((recipe) => (
                    <ListItem key={recipe.id} disablePadding>
                      <ListItemButton
                        selected={selectedRecipe?.id === recipe.id}
                        onClick={() => setSelectedRecipe(recipe)}
                      >
                        <ListItemText
                          primary={recipe.title}
                          secondary={
                            <Box component="span">
                              {recipe.category && (
                                <Chip 
                                  label={recipe.category} 
                                  size="small" 
                                  sx={{ mr: 0.5, mt: 0.5 }} 
                                />
                              )}
                              {recipe.difficulty && (
                                <Chip 
                                  label={recipe.difficulty} 
                                  size="small" 
                                  sx={{ mr: 0.5, mt: 0.5 }} 
                                />
                              )}
                              {recipe.tags?.slice(0, 3).map(tag => (
                                <Chip 
                                  key={tag.id}
                                  label={tag.tag_name} 
                                  size="small" 
                                  variant="outlined"
                                  sx={{ mr: 0.5, mt: 0.5 }} 
                                />
                              ))}
                              {recipe.tags?.length > 3 && (
                                <Chip 
                                  label={`+${recipe.tags.length - 3} more`} 
                                  size="small" 
                                  variant="outlined"
                                  sx={{ mt: 0.5 }} 
                                />
                              )}
                            </Box>
                          }
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              </>
            )}
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          onClick={handleSelectRecipe}
          variant="contained"
          disabled={!selectedRecipe}
        >
          Select
        </Button>
      </DialogActions>
    </Dialog>
  )
}
