import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  CardMedia,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  IconButton,
  TextField,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Folder as FolderIcon,
  AccessTime,
  Restaurant,
  Search as SearchIcon,
} from '@mui/icons-material';
import { collectionService, recipeService } from '../services';

const CATEGORIES = ['breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'staple', 'frozen'];
const DIFFICULTIES = ['easy', 'medium', 'hard'];

export default function Collections() {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [collectionRecipes, setCollectionRecipes] = useState([]);
  const [allRecipes, setAllRecipes] = useState([]);
  const [filteredRecipes, setFilteredRecipes] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [openAddRecipeDialog, setOpenAddRecipeDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState('create');
  const [formData, setFormData] = useState({ name: '', description: '' });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Recipe search and filter states
  const [recipeSearchTerm, setRecipeSearchTerm] = useState('');
  const [recipeCategory, setRecipeCategory] = useState('');
  const [recipeDifficulty, setRecipeDifficulty] = useState('');

  useEffect(() => {
    loadCollections();
    loadAllRecipes();
  }, []);

  useEffect(() => {
    filterRecipes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allRecipes, collectionRecipes, recipeSearchTerm, recipeCategory, recipeDifficulty]);

  const filterRecipes = () => {
    let filtered = allRecipes.filter(
      recipe => !collectionRecipes.some(cr => cr.id === recipe.id)
    );

    // Apply search filter
    if (recipeSearchTerm) {
      const searchLower = recipeSearchTerm.toLowerCase();
      filtered = filtered.filter(
        recipe =>
          recipe.title?.toLowerCase().includes(searchLower) ||
          recipe.description?.toLowerCase().includes(searchLower)
      );
    }

    // Apply category filter
    if (recipeCategory) {
      filtered = filtered.filter(recipe => recipe.category === recipeCategory);
    }

    // Apply difficulty filter
    if (recipeDifficulty) {
      filtered = filtered.filter(recipe => recipe.difficulty === recipeDifficulty);
    }

    setFilteredRecipes(filtered);
  };

  const loadCollections = async () => {
    try {
      setLoading(true);
      const response = await collectionService.getCollections();
      setCollections(response);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load collections');
      console.error('Error loading collections:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAllRecipes = async () => {
    try {
      const response = await recipeService.getRecipes({ page_size: 100 });
      // Backend now returns paginated response: { items: [], pagination: {} }
      setAllRecipes(response.items || []);
    } catch (err) {
      console.error('Error loading recipes:', err);
    }
  };

  const loadCollectionRecipes = async (collectionId) => {
    try {
      const response = await collectionService.getCollectionRecipes(collectionId);
      setCollectionRecipes(response);
    } catch (err) {
      console.error('Error loading collection recipes:', err);
      setError(err.response?.data?.detail || 'Failed to load menu items');
    }
  };

  const handleOpenDialog = (mode = 'create', collection = null) => {
    setDialogMode(mode);
    if (collection) {
      setFormData({ name: collection.name, description: collection.description || '' });
      setSelectedCollection(collection);
    } else {
      setFormData({ name: '', description: '' });
      setSelectedCollection(null);
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setFormData({ name: '', description: '' });
    setSelectedCollection(null);
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      if (dialogMode === 'create') {
        await collectionService.createCollection(formData);
      } else {
        await collectionService.updateCollection(selectedCollection.id, formData);
      }
      await loadCollections();
      handleCloseDialog();
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save collection');
      console.error('Error saving collection:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (collectionId) => {
    if (!window.confirm('Are you sure you want to delete this collection?')) return;

    try {
      setLoading(true);
      await collectionService.deleteCollection(collectionId);
      await loadCollections();
      if (selectedCollection?.id === collectionId) {
        setSelectedCollection(null);
        setCollectionRecipes([]);
      }
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete collection');
      console.error('Error deleting collection:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewCollection = async (collection) => {
    setSelectedCollection(collection);
    await loadCollectionRecipes(collection.id);
    setOpenViewDialog(true);
  };

  const handleAddRecipe = () => {
    // Reset filters when opening
    setRecipeSearchTerm('');
    setRecipeCategory('');
    setRecipeDifficulty('');
    setOpenAddRecipeDialog(true);
  };

  const handleAddRecipeSubmit = async (recipeId) => {
    if (!recipeId || !selectedCollection) return;

    try {
      setLoading(true);
      await collectionService.addRecipeToCollection(
        selectedCollection.id,
        recipeId
      );
      await loadCollectionRecipes(selectedCollection.id);
      await loadCollections(); // Reload to update item count
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add menu item to collection');
      console.error('Error adding recipe:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveRecipe = async (recipeId) => {
    if (!window.confirm('Remove this menu item from the collection?')) return;

    try {
      setLoading(true);
      await collectionService.removeRecipeFromCollection(
        selectedCollection.id,
        recipeId
      );
      await loadCollectionRecipes(selectedCollection.id);
      await loadCollections(); // Reload to update item count
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove menu item');
      console.error('Error removing recipe:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Recipe Collections
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog('create')}
          disabled={loading}
        >
          New Collection
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {collections.map((collection) => (
          <Grid item xs={12} sm={6} md={4} key={collection.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <FolderIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" component="div">
                    {collection.name}
                  </Typography>
                </Box>
                {collection.description && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {collection.description}
                  </Typography>
                )}
                <Chip
                  label={`${collection.items?.length || 0} menu items`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  onClick={() => handleViewCollection(collection)}
                >
                  View
                </Button>
                <IconButton
                  size="small"
                  onClick={() => handleOpenDialog('edit', collection)}
                  disabled={loading}
                >
                  <EditIcon fontSize="small" />
                </IconButton>
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => handleDelete(collection.id)}
                  disabled={loading}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}

        {collections.length === 0 && !loading && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="body1" color="text.secondary" align="center">
                  No collections yet. Create your first collection to organize your menu items!
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogMode === 'create' ? 'Create Collection' : 'Edit Collection'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Collection Name"
            fullWidth
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={loading || !formData.name.trim()}
          >
            {dialogMode === 'create' ? 'Create' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Collection Dialog */}
      <Dialog
        open={openViewDialog}
        onClose={() => {
          setOpenViewDialog(false);
          setSelectedCollection(null);
          setCollectionRecipes([]);
        }}
        maxWidth="md"
        fullWidth
      >
        {selectedCollection && (
          <>
            <DialogTitle>{selectedCollection.name}</DialogTitle>
            <DialogContent>
              {selectedCollection.description && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {selectedCollection.description}
                </Typography>
              )}
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Menu Items ({collectionRecipes.length})
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={handleAddRecipe}
                  size="small"
                >
                  Add Menu Item
                </Button>
              </Box>

              <List>
                {collectionRecipes.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No menu items in this collection yet. Click &quot;Add Menu Item&quot; to get started!
                  </Typography>
                ) : (
                  collectionRecipes.map((recipe) => (
                    <ListItem key={recipe.id}>
                      <ListItemText 
                        primary={recipe.title} 
                        secondary={
                          <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                            {recipe.category && (
                              <Chip label={recipe.category} size="small" />
                            )}
                            {recipe.difficulty && (
                              <Chip label={recipe.difficulty} size="small" variant="outlined" />
                            )}
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton 
                          edge="end" 
                          size="small"
                          onClick={() => handleRemoveRecipe(recipe.id)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))
                )}
              </List>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => {
                setOpenViewDialog(false);
                setSelectedCollection(null);
                setCollectionRecipes([]);
              }}>
                Close
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Add Recipe Dialog */}
      <Dialog
        open={openAddRecipeDialog}
        onClose={() => {
          setOpenAddRecipeDialog(false);
          setRecipeSearchTerm('');
          setRecipeCategory('');
          setRecipeDifficulty('');
        }}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Add Menu Item to Collection</DialogTitle>
        <DialogContent>
          {/* Search and Filters */}
          <Box sx={{ mb: 3, mt: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  placeholder="Search menu items..."
                  value={recipeSearchTerm}
                  onChange={(e) => setRecipeSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={recipeCategory}
                    label="Category"
                    onChange={(e) => setRecipeCategory(e.target.value)}
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
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Difficulty</InputLabel>
                  <Select
                    value={recipeDifficulty}
                    label="Difficulty"
                    onChange={(e) => setRecipeDifficulty(e.target.value)}
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
            </Grid>
          </Box>

          {/* Recipe Grid */}
          <Box sx={{ minHeight: 400, maxHeight: 500, overflow: 'auto' }}>
            {filteredRecipes.length === 0 ? (
              <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 4 }}>
                {allRecipes.length === 0
                  ? 'No menu items available'
                  : 'No menu items match your filters'}
              </Typography>
            ) : (
              <Grid container spacing={2}>
                {filteredRecipes.map((recipe) => {
                  const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0);
                  return (
                    <Grid item xs={12} sm={6} md={4} key={recipe.id}>
                      <Card
                        sx={{
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          '&:hover': {
                            transform: 'translateY(-4px)',
                            boxShadow: 3,
                          },
                        }}
                        onClick={() => {
                          handleAddRecipeSubmit(recipe.id);
                        }}
                      >
                        {recipe.image_url ? (
                          <CardMedia
                            component="img"
                            height="140"
                            image={recipe.image_url}
                            alt={recipe.title}
                            onError={(e) => {
                              e.target.style.display = 'none'
                              e.target.nextElementSibling.style.display = 'flex'
                            }}
                          />
                        ) : null}
                        <Box
                          sx={{
                            height: 140,
                            bgcolor: 'grey.200',
                            display: recipe.image_url ? 'none' : 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexDirection: 'column',
                            gap: 1,
                          }}
                        >
                          <Restaurant sx={{ fontSize: 40, color: 'grey.400' }} />
                          <Typography variant="caption" color="text.secondary">
                            No Image
                          </Typography>
                        </Box>
                        <CardContent>
                          <Typography variant="h6" component="div" noWrap>
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
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setOpenAddRecipeDialog(false);
            setRecipeSearchTerm('');
            setRecipeCategory('');
            setRecipeDifficulty('');
          }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
