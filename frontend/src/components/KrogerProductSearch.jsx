import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  TextField,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Snackbar,
  Collapse,
  IconButton,
  Chip,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  RadioGroup,
  FormControlLabel,
  Radio,
} from '@mui/material'
import {
  Search as SearchIcon,
  ExpandMore,
  ExpandLess,
  ShoppingCart,
  Close as CloseIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
} from '@mui/icons-material'
import { krogerService } from '../services'
import { getErrorMessage } from '../utils/errorHandler'

export default function KrogerProductSearch({ 
  groceryItems, 
  locationId,
  fulfillmentType = 'PICKUP',
  onAddToAppCart,
  disabled = false,
  searchingItem = null,
}) {
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [expandedProducts, setExpandedProducts] = useState({})
  const [bulkSearching, setBulkSearching] = useState(false)
  const [bulkSearchResults, setBulkSearchResults] = useState({})
  const [searchDialogOpen, setSearchDialogOpen] = useState(false)
  const [searchOption, setSearchOption] = useState('missing')
  const [imageModalOpen, setImageModalOpen] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null)
  const [productQuantities, setProductQuantities] = useState({})
  const [successMessage, setSuccessMessage] = useState(null)

  // Auto-search when searchingItem changes
  useEffect(() => {
    if (searchingItem && locationId) {
      setSearchTerm(searchingItem.name)
      handleSearchForItem(searchingItem.name)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchingItem, locationId])

  const getProductQuantity = (productId) => {
    return productQuantities[productId] || 1
  }

  const setProductQuantity = (productId, quantity) => {
    setProductQuantities(prev => ({
      ...prev,
      [productId]: Math.max(1, quantity)
    }))
  }

  const handleSearchForItem = async (itemName) => {
    if (!itemName || !itemName.trim() || !locationId) {
      setError('Please enter a search term and select a store location')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await krogerService.searchProducts(itemName, locationId, fulfillmentType)
      setSearchResults(data.products || [])
      if (!data.products || data.products.length === 0) {
        setError('No products found')
      }
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to search products'))
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    await handleSearchForItem(searchTerm)
  }

  const handleBulkSearch = async () => {
    if (!groceryItems || groceryItems.length === 0 || !locationId) {
      setError('No items in grocery list or location not selected')
      return
    }

    setBulkSearching(true)
    setError(null)
    const results = {}

    try {
      const itemsToSearch = searchOption === 'all' 
        ? groceryItems 
        : groceryItems.filter(item => !item.kroger_product_id)

      if (itemsToSearch.length === 0) {
        setError('All items are already linked to Kroger products')
        setBulkSearching(false)
        setSearchDialogOpen(false)
        return
      }

      for (const item of itemsToSearch) {
        try {
          const data = await krogerService.searchProducts(item.name, locationId, fulfillmentType, 0, 5)
          results[item.name] = data.products || []
        } catch (err) {
          console.error(`Failed to search for ${item.name}:`, err)
          results[item.name] = []
        }
      }
      setBulkSearchResults(results)
      setSearchResults([])
      setSearchDialogOpen(false)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to complete bulk search'))
    } finally {
      setBulkSearching(false)
    }
  }

  const handleOpenSearchDialog = () => {
    const linkedItemsCount = groceryItems.filter(item => item.kroger_product_id).length
    
    if (linkedItemsCount === 0) {
      setSearchOption('all')
      handleBulkSearch()
    } else {
      setSearchDialogOpen(true)
    }
  }

  const handleCloseSearchDialog = () => {
    setSearchDialogOpen(false)
  }

  const handleConfirmSearch = () => {
    handleBulkSearch()
  }

  const toggleExpanded = (productId) => {
    setExpandedProducts((prev) => ({
      ...prev,
      [productId]: !prev[productId],
    }))
  }

  const handleAddToAppCart = async (product) => {
    if (!onAddToAppCart) return
    
    try {
      const quantity = getProductQuantity(product.product_id)
      
      let groceryItemName = null
      if (Object.keys(bulkSearchResults).length > 0) {
        groceryItemName = Object.keys(bulkSearchResults).find(name => 
          bulkSearchResults[name].some(p => p.product_id === product.product_id)
        )
      }
      
      const cartItem = {
        product_id: product.product_id,
        upc: product.upc,
        product_name: product.description,
        brand: product.brand,
        size: product.size,
        price: product.price || product.regular_price,
        image_url: product.image_url,
        quantity: quantity,
        fulfillment_type: fulfillmentType,
        grocery_list_item_name: groceryItemName || searchingItem?.name || null,
      }
      
      await krogerService.addToAppCart(cartItem)
      
      // Notify parent that items were added
      if (onAddToAppCart) {
        onAddToAppCart()
      }
      
      // Clear quantity for this product
      setProductQuantities(prev => {
        const newQuantities = { ...prev }
        delete newQuantities[product.product_id]
        return newQuantities
      })
      
      // Show success message
      setError(null)
      const itemText = quantity > 1 ? 'items' : 'item'
      setSuccessMessage(`Successfully added ${quantity} ${itemText} to cart`)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to add item to cart'))
    }
  }

  const formatPrice = (price) => {
    if (!price) return 'Price not available'
    return `$${price.toFixed(2)}`
  }

  const renderProductCard = (product) => {
    const isExpanded = expandedProducts[product.product_id]
    const mainImage = product.image_url
    const quantity = getProductQuantity(product.product_id)

    return (
      <Card key={product.product_id} sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" gap={2}>
            {mainImage && (
              <Box
                component="img"
                src={mainImage}
                alt={product.description}
                sx={{
                  width: 80,
                  height: 80,
                  objectFit: 'contain',
                  borderRadius: 1,
                  cursor: 'pointer',
                  '&:hover': {
                    opacity: 0.8,
                  },
                }}
                onClick={() => {
                  setSelectedImage(mainImage)
                  setImageModalOpen(true)
                }}
              />
            )}

            <Box flex={1}>
              <Typography variant="h6" gutterBottom>
                {product.description}
              </Typography>
              
              <Box display="flex" gap={1} flexWrap="wrap" mb={1}>
                {product.brand && (
                  <Chip label={product.brand} size="small" variant="outlined" />
                )}
                {product.size && (
                  <Chip
                    label={product.size}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
                {product.on_sale && (
                  <Chip
                    label="ON SALE"
                    size="small"
                    color="error"
                  />
                )}
              </Box>

              <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
                {product.price || product.regular_price ? (
                  <Box>
                    {product.on_sale && product.price && product.regular_price ? (
                      <>
                        <Typography variant="h6" color="error.main" fontWeight="bold">
                          {formatPrice(product.price)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ textDecoration: 'line-through' }}>
                          {formatPrice(product.regular_price)}
                        </Typography>
                      </>
                    ) : (
                      <Typography variant="h6" color="primary">
                        {formatPrice(product.price || product.regular_price)}
                      </Typography>
                    )}
                  </Box>
                ) : (
                  <Typography variant="h6" color="text.secondary">
                    N/A
                  </Typography>
                )}
                
                {/* Quantity Selector */}
                <Box display="flex" alignItems="center" gap={1}>
                  <IconButton
                    size="small"
                    onClick={() => setProductQuantity(product.product_id, quantity - 1)}
                    disabled={quantity <= 1}
                  >
                    <RemoveIcon />
                  </IconButton>
                  <TextField
                    type="number"
                    value={quantity}
                    onChange={(e) => {
                      const val = parseInt(e.target.value)
                      if (!isNaN(val) && val > 0) {
                        setProductQuantity(product.product_id, val)
                      }
                    }}
                    size="small"
                    sx={{ width: 60 }}
                    inputProps={{ min: 1, style: { textAlign: 'center' } }}
                  />
                  <IconButton
                    size="small"
                    onClick={() => setProductQuantity(product.product_id, quantity + 1)}
                  >
                    <AddIcon />
                  </IconButton>
                </Box>

                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<ShoppingCart />}
                  onClick={() => handleAddToAppCart(product)}
                  disabled={disabled}
                >
                  {quantity > 1 ? `Add ${quantity} to Cart` : 'Add to Cart'}
                </Button>
              </Box>

              <IconButton
                size="small"
                onClick={() => toggleExpanded(product.product_id)}
                sx={{ mt: 1 }}
              >
                {isExpanded ? <ExpandLess /> : <ExpandMore />}
                <Typography variant="caption" sx={{ ml: 0.5 }}>
                  {isExpanded ? 'Less' : 'More'} Details
                </Typography>
              </IconButton>

              <Collapse in={isExpanded}>
                <Box mt={2} p={2} sx={{ bgcolor: 'action.hover' }} borderRadius={1}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">
                        Product ID
                      </Typography>
                      <Typography variant="body2">{product.product_id}</Typography>
                    </Grid>
                    
                    {product.upc && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                          UPC
                        </Typography>
                        <Typography variant="body2">{product.upc}</Typography>
                      </Grid>
                    )}
                    
                    {product.categories && product.categories.length > 0 && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                          Categories
                        </Typography>
                        <Typography variant="body2">
                          {product.categories.join(', ')}
                        </Typography>
                      </Grid>
                    )}
                    
                    {product.size && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                          Size
                        </Typography>
                        <Typography variant="body2">{product.size}</Typography>
                      </Grid>
                    )}
                    
                    {product.regular_price && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                          Regular Price
                        </Typography>
                        <Typography variant="body2">{formatPrice(product.regular_price)}</Typography>
                      </Grid>
                    )}
                    
                    {product.on_sale && product.price && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                          Sale Price
                        </Typography>
                        <Typography variant="body2" color="error.main" fontWeight="bold">
                          {formatPrice(product.price)}
                        </Typography>
                      </Grid>
                    )}
                    
                    {product.aisle_locations && product.aisle_locations.length > 0 && (
                      <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">
                          Aisle Location
                        </Typography>
                        <Typography variant="body2">
                          {product.aisle_locations.map((loc) => 
                            loc.description || `Aisle ${loc.number}`
                          ).join(', ')}
                        </Typography>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              </Collapse>
            </Box>
          </Box>
        </CardContent>
      </Card>
    )
  }

  if (disabled) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        Kroger product search is not enabled. Please contact your administrator.
      </Alert>
    )
  }

  if (!locationId) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        Please select a Kroger store location to search for products.
      </Alert>
    )
  }

  return (
    <Box>
      {/* Manual Search */}
      <Box display="flex" gap={1} mb={2}>
        <TextField
          fullWidth
          label="Search for products"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          disabled={loading}
        />
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
          onClick={handleSearch}
          disabled={loading || !searchTerm.trim()}
        >
          Search
        </Button>
      </Box>

      {/* Bulk Search */}
      {groceryItems && groceryItems.length > 0 && (
        <Button
          variant="outlined"
          fullWidth
          onClick={handleOpenSearchDialog}
          disabled={bulkSearching}
          sx={{ mb: 2 }}
        >
          {bulkSearching ? (
            <>
              <CircularProgress size={20} sx={{ mr: 1 }} />
              Searching all items...
            </>
          ) : (
            <>Search for All {groceryItems.length} Items</>
          )}
        </Button>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Search Options Dialog */}
      <Dialog open={searchDialogOpen} onClose={handleCloseSearchDialog}>
        <DialogTitle>Search for Grocery Items</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {groceryItems ? (
              <>
                {groceryItems.filter(item => item.kroger_product_id).length} of {groceryItems.length} items are already linked to Kroger products.
              </>
            ) : (
              'Loading...'
            )}
          </Typography>
          <RadioGroup
            value={searchOption}
            onChange={(e) => setSearchOption(e.target.value)}
          >
            <FormControlLabel
              value="missing"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body1">Search only missing items</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Only search for items that don&apos;t have a Kroger product linked
                  </Typography>
                </Box>
              }
            />
            <FormControlLabel
              value="all"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body1">Search all items</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Search for all items, including those already linked
                  </Typography>
                </Box>
              }
            />
          </RadioGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseSearchDialog}>Cancel</Button>
          <Button onClick={handleConfirmSearch} variant="contained" disabled={bulkSearching}>
            {bulkSearching ? 'Searching...' : 'Search'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Manual Search Results */}
      {searchResults.length > 0 && (
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Search Results ({searchResults.length})
          </Typography>
          {searchResults.map((product) => (
            <Box key={product.product_id}>
              {renderProductCard(product)}
            </Box>
          ))}
        </Box>
      )}

      {/* Bulk Search Results */}
      {Object.keys(bulkSearchResults).length > 0 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Results for Grocery Items
          </Typography>
          {Object.entries(bulkSearchResults).map(([itemName, products]) => (
            <Box key={itemName} mb={3}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                {itemName} ({products.length} {products.length === 1 ? 'match' : 'matches'})
              </Typography>
              {products.length === 0 ? (
                <Alert severity="info" sx={{ mb: 2 }}>
                  No products found for &quot;{itemName}&quot;
                </Alert>
              ) : (
                products.slice(0, 3).map((product) => (
                  <Box key={product.product_id}>
                    {renderProductCard(product)}
                  </Box>
                ))
              )}
            </Box>
          ))}
        </Box>
      )}

      {loading && searchResults.length === 0 && (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Success Snackbar */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={3000}
        onClose={() => setSuccessMessage(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSuccessMessage(null)} severity="success" sx={{ width: '100%' }}>
          {successMessage}
        </Alert>
      </Snackbar>

      {/* Image Zoom Modal */}
      <Dialog
        open={imageModalOpen}
        onClose={() => setImageModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Product Image</Typography>
            <IconButton onClick={() => setImageModalOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedImage && (
            <Box
              display="flex"
              justifyContent="center"
              alignItems="center"
              p={2}
            >
              <img
                src={selectedImage}
                alt="Product"
                style={{
                  maxWidth: '100%',
                  maxHeight: '70vh',
                  objectFit: 'contain',
                }}
              />
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  )
}
