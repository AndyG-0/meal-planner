import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  Grid,
  Rating,
  TextField,
  Card,
  CardContent,
  Alert,
  IconButton,
  Stack,
} from '@mui/material'
import {
  AccessTime,
  Restaurant,
  LocalFireDepartment,
  Add as AddIcon,
} from '@mui/icons-material'
import api from '../services/api'

export default function RecipeDetailDialog({ open, onClose, recipe, onRatingSubmitted }) {
  const [userRating, setUserRating] = useState(0)
  const [userReview, setUserReview] = useState('')
  const [ratings, setRatings] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [tags, setTags] = useState([])
  const [newTagName, setNewTagName] = useState('')
  const [newTagCategory, setNewTagCategory] = useState('')
  const [showAddTag, setShowAddTag] = useState(false)

  useEffect(() => {
    if (open && recipe) {
      loadRatings()
      loadTags()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, recipe])

  const loadRatings = async () => {
    if (!recipe?.id) return
    try {
      const response = await api.get(`/recipes/${recipe.id}/ratings`)
      setRatings(response.data || [])
    } catch (err) {
      console.error('Failed to load ratings:', err)
    }
  }

  const loadTags = async () => {
    if (!recipe?.id) return
    try {
      const response = await api.get(`/recipes/${recipe.id}`)
      setTags(response.data.tags || [])
    } catch (err) {
      console.error('Failed to load tags:', err)
    }
  }

  const handleAddTag = async () => {
    if (!newTagName.trim()) return

    try {
      await api.post(`/recipes/${recipe.id}/tags`, {
        tag_name: newTagName,
        tag_category: newTagCategory || null,
      })
      setNewTagName('')
      setNewTagCategory('')
      setShowAddTag(false)
      await loadTags()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add tag')
    }
  }

  const handleRemoveTag = async (tagId) => {
    try {
      await api.delete(`/recipes/${recipe.id}/tags/${tagId}`)
      await loadTags()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove tag')
    }
  }

  const handleSubmitRating = async () => {
    if (userRating === 0) {
      setError('Please select a rating')
      return
    }

    setSubmitting(true)
    setError('')
    
    try {
      await api.post(`/recipes/${recipe.id}/ratings`, {
        rating: userRating,
        review: userReview || null,
      })
      
      setUserRating(0)
      setUserReview('')
      await loadRatings()
      if (onRatingSubmitted) {
        onRatingSubmitted()
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit rating')
    } finally {
      setSubmitting(false)
    }
  }

  const averageRating = ratings.length > 0
    ? ratings.reduce((acc, r) => acc + r.rating, 0) / ratings.length
    : 0
  if (!recipe) return null

  const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0)

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h5">{recipe.title}</Typography>
      </DialogTitle>
      <DialogContent>
        {recipe.image_url && (
          <Box
            component="img"
            src={recipe.image_url}
            alt={recipe.title}
            sx={{ width: '100%', maxHeight: 300, objectFit: 'cover', mb: 2, borderRadius: 1 }}
          />
        )}

        {recipe.description && (
          <Typography variant="body1" paragraph>
            {recipe.description}
          </Typography>
        )}

        {/* Tags Section */}
        <Box sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" gap={2} mb={1}>
            <Typography variant="h6">Tags</Typography>
            <IconButton size="small" onClick={() => setShowAddTag(!showAddTag)}>
              <AddIcon />
            </IconButton>
          </Box>
          
          {showAddTag && (
            <Box display="flex" gap={1} mb={2}>
              <TextField
                size="small"
                label="Tag Name"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                sx={{ flexGrow: 1 }}
              />
              <TextField
                size="small"
                label="Category (optional)"
                value={newTagCategory}
                onChange={(e) => setNewTagCategory(e.target.value)}
                sx={{ flexGrow: 1 }}
                placeholder="dietary, cuisine, etc."
              />
              <Button
                variant="contained"
                size="small"
                onClick={handleAddTag}
                disabled={!newTagName.trim()}
              >
                Add
              </Button>
            </Box>
          )}

          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {tags.map((tag) => (
              <Chip
                key={tag.id}
                label={tag.tag_category ? `${tag.tag_category}: ${tag.tag_name}` : tag.tag_name}
                onDelete={() => handleRemoveTag(tag.id)}
                color="primary"
                variant="outlined"
                sx={{ mb: 1 }}
              />
            ))}
            {tags.length === 0 && !showAddTag && (
              <Typography variant="body2" color="text.secondary">
                No tags added yet
              </Typography>
            )}
          </Stack>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Ratings Section */}
        <Box sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <Typography variant="h6">Rating</Typography>
            {ratings.length > 0 && (
              <>
                <Rating value={averageRating} readOnly precision={0.5} />
                <Typography variant="body2" color="text.secondary">
                  {averageRating.toFixed(1)} ({ratings.length} review{ratings.length !== 1 ? 's' : ''})
                </Typography>
              </>
            )}
            {ratings.length === 0 && (
              <Typography variant="body2" color="text.secondary">
                No ratings yet
              </Typography>
            )}
          </Box>

          {/* Submit Rating */}
          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>
                Rate this recipe
              </Typography>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Rating
                  value={userRating}
                  onChange={(e, newValue) => setUserRating(newValue)}
                  size="large"
                />
              </Box>
              <TextField
                fullWidth
                multiline
                rows={2}
                placeholder="Write a review (optional)"
                value={userReview}
                onChange={(e) => setUserReview(e.target.value)}
                size="small"
                sx={{ mb: 1 }}
              />
              {error && (
                <Alert severity="error" sx={{ mb: 1 }}>
                  {error}
                </Alert>
              )}
              <Button
                variant="contained"
                size="small"
                onClick={handleSubmitRating}
                disabled={submitting || userRating === 0}
              >
                {submitting ? 'Submitting...' : 'Submit Rating'}
              </Button>
            </CardContent>
          </Card>

          {/* Display Reviews */}
          {ratings.filter(r => r.review).length > 0 && (
            <>
              <Typography variant="subtitle2" gutterBottom>
                Reviews
              </Typography>
              {ratings.filter(r => r.review).map((rating, index) => (
                <Card key={index} variant="outlined" sx={{ mb: 1 }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <Rating value={rating.rating} readOnly size="small" />
                      <Typography variant="body2" color="text.secondary">
                        {rating.user?.username || 'Anonymous'}
                      </Typography>
                    </Box>
                    <Typography variant="body2">{rating.review}</Typography>
                  </CardContent>
                </Card>
              ))}
            </>
          )}
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box display="flex" gap={2} mb={2} flexWrap="wrap">
          {recipe.category && (
            <Chip label={recipe.category} color="secondary" />
          )}
          {recipe.difficulty && (
            <Chip label={recipe.difficulty} color="primary" />
          )}
          {totalTime > 0 && (
            <Chip icon={<AccessTime />} label={`${totalTime} min total`} />
          )}
          {recipe.prep_time && (
            <Chip label={`Prep: ${recipe.prep_time} min`} />
          )}
          {recipe.cook_time && (
            <Chip label={`Cook: ${recipe.cook_time} min`} />
          )}
          {recipe.serving_size && (
            <Chip icon={<Restaurant />} label={`${recipe.serving_size} servings`} />
          )}
        </Box>

        {recipe.nutritional_info && (
          <>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              <LocalFireDepartment sx={{ verticalAlign: 'middle', mr: 1 }} />
              Nutritional Information
            </Typography>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              {recipe.nutritional_info.calories && (
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">
                    Calories
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {recipe.nutritional_info.calories}
                  </Typography>
                </Grid>
              )}
              {recipe.nutritional_info.protein && (
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">
                    Protein
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {recipe.nutritional_info.protein}g
                  </Typography>
                </Grid>
              )}
              {recipe.nutritional_info.carbs && (
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">
                    Carbs
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {recipe.nutritional_info.carbs}g
                  </Typography>
                </Grid>
              )}
              {recipe.nutritional_info.fat && (
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="text.secondary">
                    Fat
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {recipe.nutritional_info.fat}g
                  </Typography>
                </Grid>
              )}
            </Grid>
          </>
        )}

        <Divider sx={{ my: 2 }} />

        <Typography variant="h6" gutterBottom>
          Ingredients
        </Typography>
        <List dense>
          {recipe.ingredients?.map((ingredient, index) => {
            // Check if this is a staple recipe ingredient
            if (ingredient.ingredient_recipe_id) {
              const stapleRecipe = ingredient.ingredient_recipe || {}
              return (
                <ListItem key={index}>
                  <ListItemText
                    primary={`${ingredient.quantity} ${ingredient.unit} ${stapleRecipe.title || 'Recipe'}`}
                    secondary={
                      <>
                        <Chip 
                          label="Staple Recipe" 
                          size="small" 
                          color="secondary" 
                          sx={{ mr: 1 }}
                        />
                        {ingredient.notes && (
                          <Typography variant="caption" color="text.secondary">
                            {ingredient.notes}
                          </Typography>
                        )}
                      </>
                    }
                  />
                </ListItem>
              )
            } else {
              // Regular ingredient
              return (
                <ListItem key={index}>
                  <ListItemText
                    primary={`${ingredient.quantity} ${ingredient.unit} ${ingredient.name}`}
                    secondary={ingredient.notes}
                  />
                </ListItem>
              )
            }
          })}
        </List>

        <Divider sx={{ my: 2 }} />

        <Typography variant="h6" gutterBottom>
          Instructions
        </Typography>
        <List>
          {recipe.instructions?.map((instruction, index) => (
            <ListItem key={index} alignItems="flex-start">
              <ListItemText
                primary={
                  <Typography variant="body1">
                    <strong>Step {index + 1}:</strong> {instruction}
                  </Typography>
                }
              />
            </ListItem>
          ))}
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
