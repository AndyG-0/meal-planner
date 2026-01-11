import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  Box,
  IconButton,
  MenuItem,
  Typography,
  Alert,
  CardMedia,
  FormControl,
  InputLabel,
  Select,
  Chip,
} from '@mui/material'
import { Add as AddIcon, Delete as DeleteIcon, CloudUpload, Close, Search as SearchIcon } from '@mui/icons-material'
import api from '../services/api'
import ImageSearchDialog from './ImageSearchDialog'

const DIFFICULTY_OPTIONS = ['easy', 'medium', 'hard']
const CATEGORY_OPTIONS = ['breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'staple', 'frozen']
const COMMON_TAGS = {
  dietary: ['vegan', 'vegetarian', 'gluten-free', 'dairy-free', 'nut-free', 'keto', 'paleo', 'low-carb'],
  cuisine: ['italian', 'mexican', 'asian', 'american', 'indian', 'mediterranean'],
  other: ['quick', 'budget-friendly', 'comfort-food', 'healthy', 'kid-friendly']
}
const VISIBILITY_OPTIONS = [
  { value: 'private', label: 'Private (Only me)' },
  { value: 'group', label: 'Group (Shared with group)' },
  { value: 'public', label: 'Public (Everyone)' },
]

export default function RecipeForm({ open, onClose, onSubmit, initialData }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    serving_size: 4,
    prep_time: '',
    cook_time: '',
    difficulty: 'medium',
    category: 'dinner',
    visibility: 'private',
    group_id: '',
    is_public: false,
  })
  
  const [ingredients, setIngredients] = useState([{ name: '', quantity: '', unit: '' }])
  const [instructions, setInstructions] = useState([''])
  const [tags, setTags] = useState([])
  const [newTag, setNewTag] = useState('')
  const [newTagCategory, setNewTagCategory] = useState('dietary')
  const [nutritionalInfo, setNutritionalInfo] = useState({
    calories: '',
    protein: '',
    carbs: '',
    fat: '',
  })
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [imageSearchOpen, setImageSearchOpen] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [groups, setGroups] = useState([])
  const [stapleRecipes, setStapleRecipes] = useState([])

  // Load user's groups and staple recipes
  useEffect(() => {
    const loadData = async () => {
      try {
        const [groupsResponse, staplesResponse] = await Promise.all([
          api.get('/groups'),
          api.get('/recipes', { params: { category: 'staple', limit: 100 } })
        ])
        setGroups(groupsResponse.data)
        setStapleRecipes(staplesResponse.data)
      } catch (err) {
        console.error('Failed to load data:', err)
      }
    }
    if (open) {
      loadData()
    }
  }, [open])

  useEffect(() => {
    if (initialData) {
      setFormData({
        title: initialData.title || '',
        description: initialData.description || '',
        serving_size: initialData.serving_size || 4,
        prep_time: initialData.prep_time || '',
        cook_time: initialData.cook_time || '',
        difficulty: initialData.difficulty || 'medium',
        category: initialData.category || 'dinner',
        visibility: initialData.visibility || 'private',
        group_id: initialData.group_id || '',
        is_public: initialData.is_public || false,
      })
      setIngredients(
        initialData.ingredients?.length > 0
          ? initialData.ingredients.map(ing => ({
              ingredient_type: ing.ingredient_recipe_id ? 'staple' : 'regular',
              ingredient_recipe_id: ing.ingredient_recipe_id || '',
              name: ing.name || '',
              quantity: ing.quantity || '',
              unit: ing.unit || '',
              notes: ing.notes || ''
            }))
          : [{ ingredient_type: 'regular', name: '', quantity: '', unit: '', notes: '' }]
      )
      setInstructions(
        initialData.instructions?.length > 0 ? initialData.instructions : ['']
      )
      setTags(initialData.tags || [])
      setNutritionalInfo(
        initialData.nutritional_info || {
          calories: '',
          protein: '',
          carbs: '',
          fat: '',
        }
      )
      setImagePreview(initialData.image_url || null)
      setImageFile(null)
    } else {
      resetForm()
    }
  }, [initialData, open])

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      serving_size: 4,
      prep_time: '',
      cook_time: '',
      difficulty: 'medium',
      category: 'dinner',
      visibility: 'private',
      group_id: '',
      is_public: false,
    })
    setIngredients([{ ingredient_type: 'regular', name: '', quantity: '', unit: '', notes: '' }])
    setInstructions([''])
    setTags([])
    setNewTag('')
    setNewTagCategory('dietary')
    setNutritionalInfo({ calories: '', protein: '', carbs: '', fat: '' })
    setImageFile(null)
    setImagePreview(null)
    setError('')
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleIngredientChange = (index, field, value) => {
    const newIngredients = [...ingredients]
    
    // Handle switching between staple recipe and regular ingredient
    if (field === 'ingredient_type') {
      if (value === 'staple') {
        // Clear regular ingredient fields when switching to staple
        newIngredients[index] = {
          ingredient_type: 'staple',
          ingredient_recipe_id: '',
          quantity: newIngredients[index].quantity || '',
          unit: newIngredients[index].unit || '',
          notes: newIngredients[index].notes || ''
        }
      } else {
        // Clear staple fields when switching to regular
        newIngredients[index] = {
          ingredient_type: 'regular',
          name: '',
          quantity: newIngredients[index].quantity || '',
          unit: newIngredients[index].unit || '',
          notes: newIngredients[index].notes || ''
        }
      }
    } else {
      newIngredients[index][field] = value
    }
    
    // Validate ingredient name doesn't contain measurements (only for regular ingredients)
    if (field === 'name' && value && newIngredients[index].ingredient_type !== 'staple') {
      const trimmedValue = value.trim()
      // Check if it starts with a number or opening parenthesis
      if (trimmedValue && (trimmedValue[0].match(/[0-9(]/) || /^\d/.test(trimmedValue))) {
        setError('Warning: Ingredient names should not start with measurements. Put measurements in the Quantity and Unit fields.')
      }
      // Check if first word is an exact measurement unit
      const firstWord = trimmedValue.split(/\s+/)[0]?.toLowerCase()
      const exactUnits = ['tsp', 'tbsp', 'cup', 'cups', 'oz', 'lb', 'lbs', 'g', 'kg', 'ml', 'l', 'qt', 'gal', 'pint', 'quart']
      if (exactUnits.includes(firstWord)) {
        setError('Warning: Ingredient names should not start with measurement units. Put measurements in the Quantity and Unit fields.')
      }
    }
    
    setIngredients(newIngredients)
  }

  const handleAddIngredient = () => {
    setIngredients([...ingredients, { ingredient_type: 'regular', name: '', quantity: '', unit: '', notes: '' }])
  }

  const handleRemoveIngredient = (index) => {
    if (ingredients.length > 1) {
      setIngredients(ingredients.filter((_, i) => i !== index))
    }
  }

  const handleInstructionChange = (index, value) => {
    const newInstructions = [...instructions]
    newInstructions[index] = value
    setInstructions(newInstructions)
  }

  const handleAddInstruction = () => {
    setInstructions([...instructions, ''])
  }

  const handleRemoveInstruction = (index) => {
    if (instructions.length > 1) {
      setInstructions(instructions.filter((_, i) => i !== index))
    }
  }

  const handleNutritionalChange = (field, value) => {
    setNutritionalInfo((prev) => ({ ...prev, [field]: value }))
  }

  const handleImageChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError('Image size must be less than 5MB')
        return
      }
      if (!file.type.startsWith('image/')) {
        setError('File must be an image')
        return
      }
      setImageFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setImagePreview(reader.result)
      }
      reader.readAsDataURL(file)
      setError('')
    }
  }

  const handleRemoveImage = () => {
    setImageFile(null)
    setImagePreview(null)
  }

  const handleImageFromUrl = async (imageUrl) => {
    try {
      // Set the preview directly from URL
      setImagePreview(imageUrl)
      // We'll store the URL as a special marker so the submit handler knows to download it
      setImageFile({ url: imageUrl })
      setError('')
    } catch (err) {
      console.error('Failed to set image from URL:', err)
      setError('Failed to load image from URL')
    }
  }

  const handleAddTag = (tagName, category = 'other') => {
    const trimmedTag = tagName.trim().toLowerCase()
    if (trimmedTag && !tags.some(t => t.tag_name === trimmedTag)) {
      setTags([...tags, { tag_name: trimmedTag, tag_category: category }])
      setNewTag('')
    }
  }

  const handleRemoveTag = (tagToRemove) => {
    setTags(tags.filter(t => t.tag_name !== tagToRemove.tag_name))
  }

  const handleSubmit = async () => {
    setError('')
    
    // Validation
    if (!formData.title.trim()) {
      setError('Title is required')
      return
    }

    // Filter valid ingredients (either name or staple recipe must be set)
    const validIngredients = ingredients.filter((ing) => {
      if (ing.ingredient_type === 'staple') {
        return ing.ingredient_recipe_id
      }
      return ing.name && ing.name.trim()
    })

    // Validate ingredients (only if provided)
    for (const ing of validIngredients) {
      // Validate regular ingredients don't have measurements in name
      if (ing.ingredient_type === 'regular') {
        const name = ing.name.trim()
        // Check if name starts with number or parenthesis
        if (name && (name[0].match(/[0-9(]/))) {
          setError(`Ingredient "${name}" appears to contain measurements. Please put measurements in the Quantity and Unit fields only.`)
          return
        }
        // Check if first word is an exact measurement unit
        const firstWord = name.split(/\s+/)[0]?.toLowerCase()
        const exactUnits = ['tsp', 'tbsp', 'cup', 'cups', 'oz', 'lb', 'lbs', 'g', 'kg', 'ml', 'l', 'qt', 'gal', 'pint', 'quart']
        if (exactUnits.includes(firstWord)) {
          setError(`Ingredient "${name}" appears to start with a measurement unit. Please put measurements in the Quantity and Unit fields only.`)
          return
        }
      } else {
        // Validate staple recipe is selected
        if (!ing.ingredient_recipe_id) {
          setError('Please select a staple menu item for ingredient')
          return
        }
      }
      
      if (!ing.quantity || parseFloat(ing.quantity) <= 0) {
        const displayName = ing.ingredient_type === 'staple' 
          ? stapleRecipes.find(r => r.id === parseInt(ing.ingredient_recipe_id))?.title || 'Staple recipe'
          : ing.name
        setError(`Ingredient "${displayName}" must have a quantity greater than 0`)
        return
      }
      if (!ing.unit || !ing.unit.trim()) {
        const displayName = ing.ingredient_type === 'staple' 
          ? stapleRecipes.find(r => r.id === parseInt(ing.ingredient_recipe_id))?.title || 'Staple recipe'
          : ing.name
        setError(`Ingredient "${displayName}" must have a unit (e.g., cup, tbsp, oz, g, batch, recipe)`)
        return
      }
    }

    const validInstructions = instructions.filter((inst) => inst.trim())

    const recipeData = {
      ...formData,
      prep_time: formData.prep_time ? parseInt(formData.prep_time) : null,
      cook_time: formData.cook_time ? parseInt(formData.cook_time) : null,
      serving_size: parseInt(formData.serving_size),
      group_id: formData.group_id ? parseInt(formData.group_id) : null,
      ingredients: validIngredients.map((ing) => {
        if (ing.ingredient_type === 'staple') {
          return {
            ingredient_recipe_id: parseInt(ing.ingredient_recipe_id),
            quantity: parseFloat(ing.quantity) || 0,
            unit: ing.unit,
            notes: ing.notes || null
          }
        } else {
          return {
            name: ing.name,
            quantity: parseFloat(ing.quantity) || 0,
            unit: ing.unit,
            notes: ing.notes || null
          }
        }
      }),
      instructions: validInstructions,
      nutritional_info: Object.keys(nutritionalInfo).some((key) => nutritionalInfo[key])
        ? {
            ...nutritionalInfo,
            calories: nutritionalInfo.calories ? parseFloat(nutritionalInfo.calories) : null,
            protein: nutritionalInfo.protein ? parseFloat(nutritionalInfo.protein) : null,
            carbs: nutritionalInfo.carbs ? parseFloat(nutritionalInfo.carbs) : null,
            fat: nutritionalInfo.fat ? parseFloat(nutritionalInfo.fat) : null,
          }
        : null,
    }

    setLoading(true)
    try {
      await onSubmit(recipeData, imageFile, tags)
      onClose()
      resetForm()
    } catch (err) {
      console.error('Recipe form error:', err.response?.data)
      
      // Handle validation errors from FastAPI (422)
      if (err.response?.status === 422 && err.response?.data?.detail) {
        const detail = err.response.data.detail
        if (Array.isArray(detail)) {
          // Format validation errors
          const errorMessages = detail.map(error => {
            const field = error.loc?.slice(-1)[0] || 'field'
            return `${field}: ${error.msg}`
          }).join('; ')
          setError(errorMessages)
        } else if (typeof detail === 'string') {
          setError(detail)
        } else {
          setError('Validation error occurred')
        }
      } else {
        setError(err.response?.data?.detail || 'Failed to save menu item')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{initialData ? 'Edit Menu Item' : 'Create Menu Item'}</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={2} sx={{ mt: 1 }}>
          {/* Image Upload */}
          <Grid item xs={12}>
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Menu Item Image
              </Typography>
              {imagePreview ? (
                <Box position="relative" display="inline-block" width="100%">
                  <CardMedia
                    component="img"
                    image={imagePreview}
                    alt="Menu item preview"
                    sx={{
                      width: '100%',
                      maxHeight: 200,
                      objectFit: 'cover',
                      borderRadius: 1,
                      mb: 1,
                    }}
                  />
                  <IconButton
                    size="small"
                    onClick={handleRemoveImage}
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      bgcolor: 'background.paper',
                      '&:hover': { bgcolor: 'background.paper' },
                    }}
                  >
                    <Close />
                  </IconButton>
                </Box>
              ) : (
                <Box display="flex" gap={1}>
                  <Button
                    variant="outlined"
                    component="label"
                    startIcon={<CloudUpload />}
                    sx={{ flex: 1 }}
                  >
                    Upload Image
                    <input
                      type="file"
                      hidden
                      accept="image/*"
                      onChange={handleImageChange}
                    />
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<SearchIcon />}
                    onClick={() => setImageSearchOpen(true)}
                    sx={{ flex: 1 }}
                  >
                    Search Images
                  </Button>
                </Box>
              )}
              <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                Upload from your device or search online (max 5MB)
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Menu Item Title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Description"
              name="description"
              value={formData.description}
              onChange={handleChange}
            />
          </Grid>

          <Grid item xs={4}>
            <TextField
              fullWidth
              type="number"
              label="Serving Size"
              name="serving_size"
              value={formData.serving_size}
              onChange={handleChange}
              inputProps={{ min: 1 }}
            />
          </Grid>

          <Grid item xs={4}>
            <TextField
              fullWidth
              type="number"
              label="Prep Time (min)"
              name="prep_time"
              value={formData.prep_time}
              onChange={handleChange}
              inputProps={{ min: 0 }}
            />
          </Grid>

          <Grid item xs={4}>
            <TextField
              fullWidth
              type="number"
              label="Cook Time (min)"
              name="cook_time"
              value={formData.cook_time}
              onChange={handleChange}
              inputProps={{ min: 0 }}
            />
          </Grid>

          <Grid item xs={4}>
            <TextField
              fullWidth
              select
              label="Difficulty"
              name="difficulty"
              value={formData.difficulty}
              onChange={handleChange}
            >
              {DIFFICULTY_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={8}>
            <TextField
              fullWidth
              select
              label="Category"
              name="category"
              value={formData.category}
              onChange={handleChange}
            >
              {CATEGORY_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          {/* Tags */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Tags
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
              {tags.map((tag) => (
                <Chip
                  key={tag.tag_name}
                  label={`${tag.tag_name} ${tag.tag_category ? `(${tag.tag_category})` : ''}`}
                  onDelete={() => handleRemoveTag(tag)}
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
          </Grid>

          <Grid item xs={6}>
            <TextField
              fullWidth
              label="New Tag"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleAddTag(newTag, newTagCategory)
                }
              }}
              placeholder="e.g., vegan, gluten-free"
            />
          </Grid>

          <Grid item xs={4}>
            <TextField
              fullWidth
              select
              label="Tag Category"
              value={newTagCategory}
              onChange={(e) => setNewTagCategory(e.target.value)}
            >
              {Object.keys(COMMON_TAGS).map((category) => (
                <MenuItem key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={2}>
            <Button
              fullWidth
              variant="outlined"
              onClick={() => handleAddTag(newTag, newTagCategory)}
              disabled={!newTag.trim()}
              sx={{ height: '56px' }}
            >
              Add
            </Button>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="caption" color="textSecondary">
              Common tags by category:
            </Typography>
            {Object.entries(COMMON_TAGS).map(([category, tagList]) => (
              <Box key={category} mt={1}>
                <Typography variant="caption" fontWeight="bold">
                  {category.charAt(0).toUpperCase() + category.slice(1)}:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
                  {tagList.map((tagName) => (
                    <Chip
                      key={tagName}
                      label={tagName}
                      size="small"
                      onClick={() => handleAddTag(tagName, category)}
                      sx={{ cursor: 'pointer' }}
                    />
                  ))}
                </Box>
              </Box>
            ))}
          </Grid>

          {/* Visibility Settings */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Sharing Settings
            </Typography>
          </Grid>
          
          <Grid item xs={formData.visibility === 'group' ? 6 : 12}>
            <FormControl fullWidth>
              <InputLabel>Visibility</InputLabel>
              <Select
                name="visibility"
                value={formData.visibility}
                onChange={handleChange}
                label="Visibility"
              >
                {VISIBILITY_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {formData.visibility === 'group' && (
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Select Group</InputLabel>
                <Select
                  name="group_id"
                  value={formData.group_id}
                  onChange={handleChange}
                  label="Select Group"
                >
                  {groups.map((group) => (
                    <MenuItem key={group.id} value={group.id}>
                      {group.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {groups.length === 0 && (
                <Typography variant="caption" color="error" display="block" mt={1}>
                  No groups available. Create a group first to share with.
                </Typography>
              )}
            </Grid>
          )}

          {/* Ingredients */}
          <Grid item xs={12}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="h6">Ingredients</Typography>
              <IconButton onClick={handleAddIngredient} color="primary">
                <AddIcon />
              </IconButton>
            </Box>
            <Typography variant="caption" color="text.secondary" display="block" mb={2}>
              Add regular ingredients or select staple menu items (like sauces, doughs) as ingredients.
            </Typography>
            {ingredients.map((ingredient, index) => (
              <Box key={index} sx={{ mb: 2, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                <Grid container spacing={1}>
                  {/* Ingredient Type Selector */}
                  <Grid item xs={12}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Ingredient Type</InputLabel>
                      <Select
                        value={ingredient.ingredient_type || 'regular'}
                        onChange={(e) => handleIngredientChange(index, 'ingredient_type', e.target.value)}
                        label="Ingredient Type"
                      >
                        <MenuItem value="regular">Regular Ingredient</MenuItem>
                        <MenuItem value="staple">Staple Menu Item (Sauce, Dough, etc.)</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  {/* Regular Ingredient Fields */}
                  {ingredient.ingredient_type === 'regular' && (
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Ingredient Name"
                        placeholder="e.g., flour, sugar, salt"
                        value={ingredient.name || ''}
                        onChange={(e) => handleIngredientChange(index, 'name', e.target.value)}
                        helperText="Name only, no measurements"
                      />
                    </Grid>
                  )}

                  {/* Staple Menu Item Selector */}
                  {ingredient.ingredient_type === 'staple' && (
                    <Grid item xs={12}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Select Staple Menu Item</InputLabel>
                        <Select
                          value={ingredient.ingredient_recipe_id || ''}
                          onChange={(e) => handleIngredientChange(index, 'ingredient_recipe_id', e.target.value)}
                          label="Select Staple Menu Item"
                        >
                          {stapleRecipes.length === 0 && (
                            <MenuItem value="" disabled>
                              No staple menu items available
                            </MenuItem>
                          )}
                          {stapleRecipes.map((recipe) => (
                            <MenuItem key={recipe.id} value={recipe.id}>
                              {recipe.title}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      {stapleRecipes.length === 0 && (
                        <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                          Create menu items with category &quot;Staple&quot; first (e.g., Pizza Dough, Tomato Sauce)
                        </Typography>
                      )}
                    </Grid>
                  )}

                  {/* Quantity and Unit */}
                  <Grid item xs={5}>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="Quantity"
                      placeholder="e.g., 2"
                      value={ingredient.quantity || ''}
                      onChange={(e) => handleIngredientChange(index, 'quantity', e.target.value)}
                      inputProps={{ min: 0, step: 0.25 }}
                    />
                  </Grid>
                  <Grid item xs={5}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Unit"
                      placeholder={ingredient.ingredient_type === 'staple' ? 'e.g., batch, recipe' : 'e.g., cups, tbsp'}
                      value={ingredient.unit || ''}
                      onChange={(e) => handleIngredientChange(index, 'unit', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={2}>
                    <IconButton
                      onClick={() => handleRemoveIngredient(index)}
                      disabled={ingredients.length === 1}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Grid>

                  {/* Notes Field */}
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Notes (Optional)"
                      placeholder="e.g., softened, chopped, at room temperature"
                      value={ingredient.notes || ''}
                      onChange={(e) => handleIngredientChange(index, 'notes', e.target.value)}
                    />
                  </Grid>
                </Grid>
              </Box>
            ))}
          </Grid>

          {/* Instructions */}
          <Grid item xs={12}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="h6">Instructions</Typography>
              <IconButton onClick={handleAddInstruction} color="primary">
                <AddIcon />
              </IconButton>
            </Box>
            {instructions.map((instruction, index) => (
              <Box key={index} display="flex" gap={1} mb={1}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  placeholder={`Step ${index + 1}`}
                  value={instruction}
                  onChange={(e) => handleInstructionChange(index, e.target.value)}
                />
                <IconButton
                  onClick={() => handleRemoveInstruction(index)}
                  disabled={instructions.length === 1}
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            ))}
          </Grid>

          {/* Nutritional Info */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Nutritional Information (Optional)
            </Typography>
          </Grid>
          <Grid item xs={3}>
            <TextField
              fullWidth
              type="number"
              label="Calories"
              value={nutritionalInfo.calories}
              onChange={(e) => handleNutritionalChange('calories', e.target.value)}
              inputProps={{ min: 0 }}
            />
          </Grid>
          <Grid item xs={3}>
            <TextField
              fullWidth
              type="number"
              label="Protein (g)"
              value={nutritionalInfo.protein}
              onChange={(e) => handleNutritionalChange('protein', e.target.value)}
              inputProps={{ min: 0 }}
            />
          </Grid>
          <Grid item xs={3}>
            <TextField
              fullWidth
              type="number"
              label="Carbs (g)"
              value={nutritionalInfo.carbs}
              onChange={(e) => handleNutritionalChange('carbs', e.target.value)}
              inputProps={{ min: 0 }}
            />
          </Grid>
          <Grid item xs={3}>
            <TextField
              fullWidth
              type="number"
              label="Fat (g)"
              value={nutritionalInfo.fat}
              onChange={(e) => handleNutritionalChange('fat', e.target.value)}
              inputProps={{ min: 0 }}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" disabled={loading}>
          {loading ? 'Saving...' : initialData ? 'Update' : 'Create'}
        </Button>
      </DialogActions>

      {/* Image Search Dialog */}
      <ImageSearchDialog
        open={imageSearchOpen}
        onClose={() => setImageSearchOpen(false)}
        onSelectImage={handleImageFromUrl}
        initialQuery={formData.title}
      />
    </Dialog>
  )
}
