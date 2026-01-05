import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardMedia,
  CardContent,
  CardActions,
  IconButton,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material'
import {
  Add as AddIcon,
  Favorite,
  FavoriteBorder,
  Edit as EditIcon,
  Delete as DeleteIcon,
  AccessTime,
  Restaurant,
  SmartToy as AIIcon,
  FileDownload as ExportIcon,
  FileUpload as ImportIcon,
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterIcon,
  Search as SearchIcon,
} from '@mui/icons-material'
import { recipeService } from '../services'
import { useRecipeStore } from '../store/recipeStore'
import RecipeForm from '../components/RecipeForm'
import RecipeDetailDialog from '../components/RecipeDetailDialog'
import AIRecipeChat from '../components/AIRecipeChat'

const DIFFICULTIES = ['easy', 'medium', 'hard']
const CATEGORIES = ['breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'staple', 'frozen']

export default function Recipes() {
  const {
    recipes,
    setRecipes,
    selectedRecipe,
    setSelectedRecipe,
    addRecipe,
    updateRecipe,
    deleteRecipe,
    loading,
    setLoading,
    error,
    setError,
    clearError,
  } = useRecipeStore()

  const [searchTerm, setSearchTerm] = useState('')
  const [openForm, setOpenForm] = useState(false)
  const [openDetail, setOpenDetail] = useState(false)
  const [openAIChat, setOpenAIChat] = useState(false)
  const [aiEnabled, setAiEnabled] = useState(false)
  const [editingRecipe, setEditingRecipe] = useState(null)
  const [activeTab, setActiveTab] = useState(0) // 0 = All Recipes, 1 = Favorites, 2 = Staples
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [importFile, setImportFile] = useState(null)
  
  // Advanced filters
  const [selectedCategory, setSelectedCategory] = useState('')
  const [selectedDifficulty, setSelectedDifficulty] = useState('')
  const [selectedTags, setSelectedTags] = useState([])
  const [maxPrepTime, setMaxPrepTime] = useState('')
  const [maxCookTime, setMaxCookTime] = useState('')
  const [allTagsList, setAllTagsList] = useState([])
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)

  useEffect(() => {
    loadRecipes()
    checkAIFeature()
    loadTags()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]) // Reload when tab changes

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

  const loadRecipes = async () => {
    setLoading(true)
    clearError()
    setCurrentPage(1)
    try {
      let params = { search: searchTerm, page: 1, page_size: 20 }
      
      // Add filters
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
      
      // Add category filter based on active tab
      if (activeTab === 2) {
        // Staple recipes tab
        params.category = 'staple'
      } else if (activeTab === 1) {
        // Favorites tab - handled separately below
        params = { page: 1, page_size: 20 }
      }
      
      let data
      if (activeTab === 1) {
        // Load favorites
        const response = await recipeService.getRecipes({ ...params, search: searchTerm })
        // Backend returns paginated response: { items: [], pagination: {} }
        data = response.items.filter(recipe => recipe.is_favorite)
        setHasMore(response.pagination.has_next)
      } else {
        const response = await recipeService.getRecipes(params)
        data = response.items
        setHasMore(response.pagination.has_next)
      }
      
      setRecipes(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load recipes')
    } finally {
      setLoading(false)
    }
  }

  const loadMoreRecipes = async () => {
    if (loadingMore || !hasMore) return
    
    setLoadingMore(true)
    clearError()
    try {
      const nextPage = currentPage + 1
      let params = { search: searchTerm, page: nextPage, page_size: 20 }
      
      // Add all the same filters
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
      
      if (activeTab === 2) {
        params.category = 'staple'
      } else if (activeTab === 1) {
        params = { page: nextPage, page_size: 20 }
      }
      
      let newRecipes
      if (activeTab === 1) {
        const response = await recipeService.getRecipes({ ...params, search: searchTerm })
        newRecipes = response.items.filter(recipe => recipe.is_favorite)
        setHasMore(response.pagination.has_next)
      } else {
        const response = await recipeService.getRecipes(params)
        newRecipes = response.items
        setHasMore(response.pagination.has_next)
      }
      
      setRecipes([...recipes, ...newRecipes])
      setCurrentPage(nextPage)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load more recipes')
    } finally {
      setLoadingMore(false)
    }
  }

  const checkAIFeature = async () => {
    try {
      const response = await recipeService.checkFeature('ai_recipe_creation')
      setAiEnabled(response.enabled)
    } catch (err) {
      // Feature not available
      setAiEnabled(false)
    }
  }

  const handleAIRecipeCreated = (recipe) => {
    addRecipe(recipe)
    loadRecipes() // Reload to ensure we have the latest
  }

  const handleSearch = () => {
    loadRecipes()
  }

  const handleClearFilters = () => {
    setSearchTerm('')
    setSelectedCategory('')
    setSelectedDifficulty('')
    setSelectedTags([])
    setMaxPrepTime('')
    setMaxCookTime('')
  }

  const handleCreateRecipe = async (recipeData, imageFile, tags) => {
    const newRecipe = await recipeService.createRecipe(recipeData)
    
    // Add tags if provided
    if (tags && tags.length > 0) {
      for (const tag of tags) {
        try {
          await recipeService.addTag(newRecipe.id, tag.tag_name, tag.tag_category)
        } catch (err) {
          console.warn('Failed to add tag:', tag.tag_name, err)
        }
      }
    }
    
    // Upload image if provided
    if (imageFile) {
      const formData = new FormData()
      
      // Check if imageFile is a URL object (from image search) or a File object (from upload)
      if (imageFile.url) {
        // Download image from URL and convert to blob
        try {
          const response = await fetch(imageFile.url)
          const blob = await response.blob()
          // Create a file from the blob
          const file = new File([blob], 'recipe-image.jpg', { type: blob.type })
          formData.append('file', file)
        } catch (err) {
          console.warn('Failed to download image from URL:', err)
          // Continue without image
        }
      } else {
        // Regular file upload
        formData.append('file', imageFile)
      }
      
      if (formData.has('file')) {
        await recipeService.uploadImage(newRecipe.id, formData)
      }
      
      // Reload the recipe to get the updated image URL
      const updatedRecipe = await recipeService.getRecipe(newRecipe.id)
      addRecipe(updatedRecipe)
    } else {
      // Reload to get tags
      const updatedRecipe = await recipeService.getRecipe(newRecipe.id)
      addRecipe(updatedRecipe)
    }
    
    setOpenForm(false)
    setEditingRecipe(null)
  }

  const handleUpdateRecipe = async (recipeData, imageFile, tags) => {
    await recipeService.updateRecipe(editingRecipe.id, recipeData)
    
    // Delete existing tags and add new ones
    if (tags) {
      // Get current tags to delete
      const currentRecipe = await recipeService.getRecipe(editingRecipe.id)
      if (currentRecipe.tags) {
        for (const tag of currentRecipe.tags) {
          try {
            await recipeService.removeTag(editingRecipe.id, tag.id)
          } catch (err) {
            console.warn('Failed to remove tag:', tag.tag_name, err)
          }
        }
      }
      
      // Add new tags
      for (const tag of tags) {
        try {
          await recipeService.addTag(editingRecipe.id, tag.tag_name, tag.tag_category)
        } catch (err) {
          console.warn('Failed to add tag:', tag.tag_name, err)
        }
      }
    }
    
    // Upload image if provided
    if (imageFile) {
      const formData = new FormData()
      
      // Check if imageFile is a URL object (from image search) or a File object (from upload)
      if (imageFile.url) {
        // Download image from URL and convert to blob
        try {
          const response = await fetch(imageFile.url)
          const blob = await response.blob()
          // Create a file from the blob
          const file = new File([blob], 'recipe-image.jpg', { type: blob.type })
          formData.append('file', file)
        } catch (err) {
          console.warn('Failed to download image from URL:', err)
          // Continue without image
        }
      } else {
        // Regular file upload
        formData.append('file', imageFile)
      }
      
      if (formData.has('file')) {
        await recipeService.uploadImage(editingRecipe.id, formData)
      }
      
      // Reload the recipe to get the updated image URL
      const updatedRecipe = await recipeService.getRecipe(editingRecipe.id)
      updateRecipe(editingRecipe.id, updatedRecipe)
    } else {
      // Reload to get tags
      const updatedRecipe = await recipeService.getRecipe(editingRecipe.id)
      updateRecipe(editingRecipe.id, updatedRecipe)
    }
    
    setOpenForm(false)
    setEditingRecipe(null)
  }

  const handleDeleteRecipe = async (id) => {
    if (window.confirm('Are you sure you want to delete this recipe?')) {
      try {
        await recipeService.deleteRecipe(id)
        deleteRecipe(id)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to delete recipe')
      }
    }
  }

  const handleViewDetails = async (recipe) => {
    setSelectedRecipe(recipe)
    setOpenDetail(true)
  }

  const handleEdit = (recipe) => {
    setEditingRecipe(recipe)
    setOpenForm(true)
  }

  const handleToggleFavorite = async (recipe, isFavorited) => {
    try {
      if (isFavorited) {
        await recipeService.unfavoriteRecipe(recipe.id)
      } else {
        await recipeService.favoriteRecipe(recipe.id)
      }
      // Reload recipes to update favorites
      loadRecipes()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update favorite')
    }
  }

  const getTotalTime = (recipe) => {
    const prep = recipe.prep_time || 0
    const cook = recipe.cook_time || 0
    return prep + cook
  }

  const handleExport = async () => {
    try {
      const response = await recipeService.exportRecipes()
      const blob = new Blob([JSON.stringify(response.data)], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `recipes_${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to export recipes')
    }
  }

  const handleImport = async () => {
    if (!importFile) return

    const formData = new FormData()
    formData.append('file', importFile)

    try {
      const result = await recipeService.importRecipes(formData)
      setImportDialogOpen(false)
      setImportFile(null)
      alert(`Successfully imported ${result.imported} recipes`)
      loadRecipes()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to import recipes')
    }
  }

  if (loading && recipes.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Recipes
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<ImportIcon />}
            onClick={() => setImportDialogOpen(true)}
            size="small"
          >
            Import
          </Button>
          <Button
            variant="outlined"
            startIcon={<ExportIcon />}
            onClick={handleExport}
            size="small"
          >
            Export
          </Button>
          {aiEnabled && (
            <Button
              variant="outlined"
              startIcon={<AIIcon />}
              onClick={() => setOpenAIChat(true)}
              color="secondary"
            >
              Create with AI
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setEditingRecipe(null)
              setOpenForm(true)
            }}
          >
            Add Recipe
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" onClose={clearError} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Search and Filters */}
      <Box sx={{ mb: 3 }}>
        <Box display="flex" gap={2} mb={2}>
          <TextField
            fullWidth
            placeholder="Search recipes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
          />
          <Button variant="contained" onClick={handleSearch}>
            Search
          </Button>
        </Box>

        {/* Advanced Filters */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <FilterIcon />
              <Typography>
                Advanced Filters
                {(selectedCategory || selectedDifficulty || selectedTags.length > 0 || maxPrepTime || maxCookTime) && (
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
              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={selectedCategory}
                    label="Category"
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    disabled={activeTab === 2} // Disable when on Staples tab
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
              <Grid item xs={12} sm={6} md={4}>
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

              {/* Max Prep Time */}
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="Max Prep Time (minutes)"
                  value={maxPrepTime}
                  onChange={(e) => setMaxPrepTime(e.target.value)}
                  inputProps={{ min: 0 }}
                />
              </Grid>

              {/* Max Cook Time */}
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="Max Cook Time (minutes)"
                  value={maxCookTime}
                  onChange={(e) => setMaxCookTime(e.target.value)}
                  inputProps={{ min: 0 }}
                />
              </Grid>

              {/* Tags Filter */}
              <Grid item xs={12} md={8}>
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

              {/* Clear Filters Button */}
              <Grid item xs={12}>
                <Box display="flex" justifyContent="space-between">
                  <Button 
                    onClick={handleClearFilters} 
                    disabled={!selectedCategory && !selectedDifficulty && selectedTags.length === 0 && !maxPrepTime && !maxCookTime}
                  >
                    Clear All Filters
                  </Button>
                  <Button 
                    variant="contained" 
                    onClick={handleSearch}
                    startIcon={<SearchIcon />}
                  >
                    Apply Filters
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      </Box>

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 2 }}>
        <Tab label="All Recipes" />
        <Tab label="Favorites" icon={<Favorite sx={{ ml: 1 }} />} iconPosition="end" />
        <Tab label="Staple Recipes" />
      </Tabs>

      {activeTab === 2 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Staple recipes are base ingredients like sauces, doughs, or stocks that can be used as ingredients in other recipes. 
          Create a recipe with category &quot;Staple&quot; to see it here.
        </Alert>
      )}

      <Grid container spacing={3}>
        {recipes.map((recipe) => {
          const totalTime = getTotalTime(recipe)
          const isFavorited = recipe.is_favorite || false

          return (
            <Grid item xs={12} sm={6} md={4} key={recipe.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardMedia
                  component="img"
                  height="200"
                  image={recipe.image_url || 'https://via.placeholder.com/400x200?text=No+Image'}
                  alt={recipe.title}
                  sx={{ cursor: 'pointer' }}
                  onClick={() => handleViewDetails(recipe)}
                />
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography
                    gutterBottom
                    variant="h6"
                    component="div"
                    sx={{ cursor: 'pointer' }}
                    onClick={() => handleViewDetails(recipe)}
                  >
                    {recipe.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" noWrap>
                    {recipe.description}
                  </Typography>
                  <Box display="flex" gap={1} mt={1} flexWrap="wrap">
                    {recipe.category && (
                      <Chip label={recipe.category} size="small" color="secondary" />
                    )}
                    {recipe.difficulty && (
                      <Chip label={recipe.difficulty} size="small" />
                    )}
                    {totalTime > 0 && (
                      <Chip
                        icon={<AccessTime />}
                        label={`${totalTime} min`}
                        size="small"
                      />
                    )}
                    {recipe.serving_size && (
                      <Chip
                        icon={<Restaurant />}
                        label={`${recipe.serving_size} servings`}
                        size="small"
                      />
                    )}
                  </Box>
                  {recipe.tags && recipe.tags.length > 0 && (
                    <Box display="flex" gap={0.5} mt={1} flexWrap="wrap">
                      {recipe.tags.slice(0, 3).map((tag) => (
                        <Chip
                          key={tag.id}
                          label={tag.tag_name}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                      ))}
                      {recipe.tags.length > 3 && (
                        <Chip label={`+${recipe.tags.length - 3}`} size="small" variant="outlined" />
                      )}
                    </Box>
                  )}
                </CardContent>
                <CardActions>
                  <IconButton
                    onClick={() => handleToggleFavorite(recipe, isFavorited)}
                    color="error"
                  >
                    {isFavorited ? <Favorite /> : <FavoriteBorder />}
                  </IconButton>
                  <IconButton onClick={() => handleEdit(recipe)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDeleteRecipe(recipe.id)}>
                    <DeleteIcon />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          )
        })}
      </Grid>

      {/* Load More Button */}
      {hasMore && (
        <Box display="flex" justifyContent="center" mt={4}>
          <Button
            variant="outlined"
            onClick={loadMoreRecipes}
            disabled={loadingMore}
            size="large"
          >
            {loadingMore ? <CircularProgress size={24} /> : 'Load More Recipes'}
          </Button>
        </Box>
      )}

      {/* Loading indicator for infinite scroll */}
      {loadingMore && (
        <Box display="flex" justifyContent="center" mt={2}>
          <CircularProgress />
        </Box>
      )}

      <RecipeForm
        open={openForm}
        onClose={() => {
          setOpenForm(false)
          setEditingRecipe(null)
        }}
        onSubmit={editingRecipe ? handleUpdateRecipe : handleCreateRecipe}
        initialData={editingRecipe}
      />

      <RecipeDetailDialog
        open={openDetail}
        onClose={() => {
          setOpenDetail(false)
          setSelectedRecipe(null)
        }}
        recipe={selectedRecipe}
        onRatingSubmitted={loadRecipes}
      />

      <AIRecipeChat
        open={openAIChat}
        onClose={() => setOpenAIChat(false)}
        onRecipeCreated={handleAIRecipeCreated}
      />

      <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Import Recipes</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Select a JSON file containing recipes to import.
          </Typography>
          <input
            type="file"
            accept="application/json"
            onChange={(e) => setImportFile(e.target.files[0])}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleImport} variant="contained" disabled={!importFile}>
            Import
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

