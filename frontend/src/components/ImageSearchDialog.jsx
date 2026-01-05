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
  CircularProgress,
  Typography,
  Card,
  CardMedia,
  CardActionArea,
  Alert,
  IconButton,
} from '@mui/material'
import { Search as SearchIcon, Close as CloseIcon } from '@mui/icons-material'
import api from '../services/api'

export default function ImageSearchDialog({ open, onClose, onSelectImage, initialQuery = '' }) {
  const [query, setQuery] = useState(initialQuery)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedImage, setSelectedImage] = useState(null)

  // Update query when initialQuery changes or dialog opens
  useEffect(() => {
    if (open && initialQuery) {
      setQuery(initialQuery)
    }
  }, [open, initialQuery])

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }

    setError('')
    setLoading(true)
    
    try {
      const response = await api.get('/ai/search-images', {
        params: {
          query: query.trim(),
          max_results: 20,
        },
      })
      
      if (response.data.success) {
        setResults(response.data.results || [])
        if (response.data.results.length === 0) {
          setError('No images found. Try a different search term.')
        }
      } else {
        setError('Failed to search for images')
      }
    } catch (err) {
      console.error('Image search error:', err)
      setError(err.response?.data?.detail || 'Failed to search for images')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const handleSelectImage = (image) => {
    setSelectedImage(image)
  }

  const handleConfirmSelection = () => {
    if (selectedImage) {
      onSelectImage(selectedImage.url)
      handleClose()
    }
  }

  const handleClose = () => {
    setQuery(initialQuery)
    setResults([])
    setError('')
    setSelectedImage(null)
    onClose()
  }

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <DialogTitle>
        Search for Recipe Image
        <IconButton
          onClick={handleClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 3, display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            placeholder="Search for food images (e.g., 'chocolate cake', 'pasta carbonara')"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
            autoFocus
          />
          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
            sx={{ minWidth: 120 }}
          >
            {loading ? 'Searching...' : 'Search'}
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {selectedImage && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Selected image from: {new URL(selectedImage.source).hostname}
          </Alert>
        )}

        {results.length > 0 ? (
          <Grid container spacing={2} sx={{ maxHeight: 'calc(80vh - 220px)', overflowY: 'auto' }}>
            {results.map((image, index) => (
              <Grid item xs={6} sm={4} md={3} key={index}>
                <Card 
                  sx={{ 
                    border: selectedImage?.url === image.url ? 3 : 0,
                    borderColor: 'primary.main',
                    cursor: 'pointer',
                  }}
                >
                  <CardActionArea onClick={() => handleSelectImage(image)}>
                    <CardMedia
                      component="img"
                      height="200"
                      image={image.thumbnail || image.url}
                      alt={image.title || 'Recipe image'}
                      sx={{ 
                        objectFit: 'cover',
                        backgroundColor: '#f5f5f5',
                      }}
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle"%3ENo Image%3C/text%3E%3C/svg%3E'
                      }}
                    />
                    {image.title && (
                      <Box sx={{ p: 1, backgroundColor: 'rgba(0,0,0,0.7)', color: 'white' }}>
                        <Typography variant="caption" noWrap>
                          {image.title}
                        </Typography>
                      </Box>
                    )}
                  </CardActionArea>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : !loading && query && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              Search for images to find the perfect photo for your recipe
            </Typography>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button 
          onClick={handleConfirmSelection} 
          variant="contained" 
          disabled={!selectedImage}
        >
          Use Selected Image
        </Button>
      </DialogActions>
    </Dialog>
  )
}
