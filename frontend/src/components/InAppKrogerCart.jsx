import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import {
  Delete as DeleteIcon,
  ShoppingCart as ShoppingCartIcon,
  Send as SendIcon,
  DeleteSweep as ClearAllIcon,
  Close as CloseIcon,
} from '@mui/icons-material'
import { krogerService, groceryListService } from '../services'
import { getErrorMessage } from '../utils/errorHandler'

export default function InAppKrogerCart({ 
  onCartChange,
  initialFulfillmentType = 'PICKUP',
  listId = null,
  groceryItems = null,
  onItemUnlinked = null,
}) {
  const [cart, setCart] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sendDialogOpen, setSendDialogOpen] = useState(false)
  const [sending, setSending] = useState(false)
  const [fulfillmentType, setFulfillmentType] = useState(initialFulfillmentType)
  const [imageModalOpen, setImageModalOpen] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null)

  useEffect(() => {
    loadCart()
    // Set up polling to refresh cart every 3 seconds
    const interval = setInterval(() => {
      loadCart(true) // Silent refresh
    }, 3000)
    return () => clearInterval(interval)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadCart = async (silent = false) => {
    if (!silent) {
      setLoading(true)
    }
    setError(null)
    try {
      const data = await krogerService.getAppCart()
      setCart(data)
      if (data.fulfillment_type) {
        setFulfillmentType(data.fulfillment_type)
      }
      if (onCartChange) {
        onCartChange(data)
      }
    } catch (err) {
      if (!silent) {
        setError(getErrorMessage(err.response?.data?.detail, 'Failed to load cart'))
      }
    } finally {
      if (!silent) {
        setLoading(false)
      }
    }
  }

  const handleRemoveItem = async (itemId) => {
    try {
      // Get the item before removing to check if it's linked
      const itemToRemove = cart?.items?.find(item => item.id === itemId)
      
      await krogerService.removeFromAppCart(itemId)
      
      // If the item was linked to a grocery list item, unlink it
      if (itemToRemove?.grocery_list_item_name && listId && groceryItems) {
        const updatedItems = groceryItems.map(item => {
          if (item.name === itemToRemove.grocery_list_item_name && item.kroger_product_id) {
            // Remove Kroger product info and uncheck
            // eslint-disable-next-line no-unused-vars
            const { kroger_product_id, kroger_upc, kroger_price, kroger_product_name, ...rest } = item
            return {
              ...rest,
              checked: false,
            }
          }
          return item
        })
        
        await groceryListService.updateGroceryList(listId, updatedItems)
        
        // Notify parent to reload grocery list
        if (onItemUnlinked) {
          onItemUnlinked()
        }
      }
      
      await loadCart()
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to remove item'))
    }
  }

  const handleUpdateQuantity = async (itemId, newQuantity) => {
    if (newQuantity < 1) return
    
    try {
      await krogerService.updateCartItem(itemId, { quantity: newQuantity })
      await loadCart()
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to update quantity'))
    }
  }

  const handleClearCart = async () => {
    if (!window.confirm('Are you sure you want to clear your cart?')) return

    try {
      // If items are linked to grocery list, unlink them
      if (cart?.items && listId && groceryItems) {
        const linkedItemNames = cart.items
          .filter(item => item.grocery_list_item_name)
          .map(item => item.grocery_list_item_name)
        
        if (linkedItemNames.length > 0) {
          const updatedItems = groceryItems.map(item => {
            if (linkedItemNames.includes(item.name) && item.kroger_product_id) {
              // Remove Kroger product info and uncheck
              // eslint-disable-next-line no-unused-vars
              const { kroger_product_id, kroger_upc, kroger_price, kroger_product_name, ...rest } = item
              return {
                ...rest,
                checked: false,
              }
            }
            return item
          })
          
          await groceryListService.updateGroceryList(listId, updatedItems)
          
          // Notify parent to reload grocery list
          if (onItemUnlinked) {
            onItemUnlinked()
          }
        }
      }
      
      await krogerService.clearAppCart()
      await loadCart()
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to clear cart'))
    }
  }

  const handleFulfillmentChange = async (newType) => {
    if (cart && cart.total_items > 0) {
      if (!window.confirm(
        `Changing fulfillment type from ${fulfillmentType} to ${newType} will empty your cart. Continue?`
      )) {
        return
      }
      
      try {
        await krogerService.clearAppCart()
        setFulfillmentType(newType)
        await loadCart()
      } catch (err) {
        setError(getErrorMessage(err.response?.data?.detail, 'Failed to change fulfillment type'))
      }
    } else {
      setFulfillmentType(newType)
    }
  }

  const handleSendToKroger = async () => {
    setSending(true)
    try {
      const result = await krogerService.sendCartToKroger(true)
      
      if (result.success) {
        alert(`Successfully sent ${result.items_sent} items to Kroger! 

IMPORTANT: These items are now in your Kroger cart and can no longer be managed in the Meal Planner app. You must make any changes directly on Kroger's website.

You can clear this cart and start over if you want to add more items.`)
        
        // Don't auto-clear - let user decide when to clear
      } else {
        setError(result.message)
      }

      if (result.errors && result.errors.length > 0) {
        setError(`Some items failed to send: ${result.errors.join(', ')}`)
      }
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to send cart to Kroger'))
    } finally {
      setSending(false)
      setSendDialogOpen(false)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Fulfillment Type Selector */}
      <Box sx={{ mb: 2 }}>
        <FormControl fullWidth size="small">
          <InputLabel>Fulfillment Type</InputLabel>
          <Select
            value={fulfillmentType}
            label="Fulfillment Type"
            onChange={(e) => handleFulfillmentChange(e.target.value)}
          >
            <MenuItem value="PICKUP">Pickup</MenuItem>
            <MenuItem value="DELIVERY">Delivery</MenuItem>
          </Select>
        </FormControl>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
          {cart && cart.total_items > 0 
            ? 'Changing this will empty your cart'
            : 'Select how you want to receive your items'}
        </Typography>
      </Box>

      {/* Cart Summary */}
      {cart && cart.total_items > 0 && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="h6">
                {cart.total_items} {cart.total_items === 1 ? 'Product' : 'Products'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {cart.total_quantity} {cart.total_quantity === 1 ? 'item' : 'items'} total
              </Typography>
            </Box>
            {cart.estimated_total && (
              <Typography variant="h5" color="success.main" fontWeight="bold">
                ${cart.estimated_total.toFixed(2)}
              </Typography>
            )}
          </Box>
        </Paper>
      )}

      {/* Cart Items */}
      {cart && cart.items && cart.items.length > 0 ? (
        <List>
          {cart.items.map((item) => (
            <ListItem key={item.id} divider>
              {item.image_url && (
                <Box
                  component="img"
                  src={item.image_url}
                  alt={item.product_name}
                  sx={{
                    width: 60,
                    height: 60,
                    objectFit: 'contain',
                    borderRadius: 1,
                    mr: 2,
                    cursor: 'pointer',
                    '&:hover': {
                      opacity: 0.8,
                    },
                  }}
                  onClick={() => {
                    setSelectedImage(item.image_url)
                    setImageModalOpen(true)
                  }}
                />
              )}
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body1">{item.product_name}</Typography>
                    {item.grocery_list_item_name && (
                      <Chip
                        label={`For: ${item.grocery_list_item_name}`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    )}
                  </Box>
                }
                secondary={
                  <Box>
                    {item.brand && (
                      <Typography variant="caption" display="block">
                        Brand: {item.brand}
                      </Typography>
                    )}
                    {item.size && (
                      <Typography variant="caption" display="block">
                        Size: {item.size}
                      </Typography>
                    )}
                    {item.price && (
                      <Typography variant="caption" display="block" color="success.main">
                        ${item.price.toFixed(2)} each
                      </Typography>
                    )}
                    <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                        disabled={item.quantity <= 1}
                      >
                        -
                      </Button>
                      <TextField
                        type="number"
                        value={item.quantity}
                        onChange={(e) => {
                          const val = parseInt(e.target.value)
                          if (!isNaN(val) && val > 0) {
                            handleUpdateQuantity(item.id, val)
                          }
                        }}
                        size="small"
                        sx={{ width: 60 }}
                        inputProps={{ min: 1, style: { textAlign: 'center' } }}
                      />
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                      >
                        +
                      </Button>
                      {item.price && (
                        <Typography variant="body2" fontWeight="bold" sx={{ ml: 'auto' }}>
                          ${(item.price * item.quantity).toFixed(2)}
                        </Typography>
                      )}
                    </Box>
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => handleRemoveItem(item.id)}
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      ) : (
        <Paper variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
          <ShoppingCartIcon sx={{ fontSize: 60, color: 'action.disabled', mb: 1 }} />
          <Typography color="text.secondary">
            Your cart is empty
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Search for products and add them to your cart
          </Typography>
        </Paper>
      )}

      {/* Action Buttons */}
      {cart && cart.items && cart.items.length > 0 && (
        <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<SendIcon />}
            onClick={() => setSendDialogOpen(true)}
            disabled={sending}
            fullWidth
          >
            Send to Kroger ({cart.total_quantity} {cart.total_quantity === 1 ? 'item' : 'items'})
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<ClearAllIcon />}
            onClick={handleClearCart}
            fullWidth
          >
            Clear Cart
          </Button>
        </Box>
      )}

      {/* Send Confirmation Dialog */}
      <Dialog open={sendDialogOpen} onClose={() => setSendDialogOpen(false)}>
        <DialogTitle>Send Cart to Kroger?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            You are about to send {cart?.total_quantity || 0} items to your Kroger cart.
          </DialogContentText>
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2" fontWeight="bold" gutterBottom>
              Important:
            </Typography>
            <Typography variant="body2">
              • Once sent, items can only be managed on Kroger&apos;s website
              <br />
              • You cannot remove or modify them from this app
              <br />
              • Clear this cart after sending if you want to add more items
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSendDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSendToKroger}
            variant="contained"
            color="primary"
            disabled={sending}
            startIcon={sending ? <CircularProgress size={20} /> : <SendIcon />}
          >
            {sending ? 'Sending...' : 'Confirm & Send'}
          </Button>
        </DialogActions>
      </Dialog>

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
