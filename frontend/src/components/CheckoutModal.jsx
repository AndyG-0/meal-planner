import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Card,
  CardContent,
  CardMedia,
  Chip,
  Checkbox,
  FormControlLabel,
  Radio,
} from '@mui/material'
import { ShoppingCart as ShoppingCartIcon } from '@mui/icons-material'

export default function CheckoutModal({
  open,
  items,
  matchedProducts,
  krogerEnabled,
  krogerCartEnabled,
  onConfirm,
  onClose,
}) {
  const [selectedProductsByItem, setSelectedProductsByItem] = useState({})
  const [addToCart, setAddToCart] = useState(true)

  const handleSelectProduct = (itemName, product) => {
    setSelectedProductsByItem(prev => ({
      ...prev,
      [itemName]: prev[itemName]?.product_id === product.product_id ? null : product,
    }))
  }

  const handleConfirm = () => {
    onConfirm(selectedProductsByItem)
    setSelectedProductsByItem({})
    setAddToCart(true)
  }

  if (!items || items.length === 0) {
    return null
  }

  const selectedCount = Object.values(selectedProductsByItem).filter(Boolean).length

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Check off Items
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {items.length} item(s) ready to checkout. Match them with Kroger products to add to your cart.
          </Typography>

          {krogerCartEnabled && matchedProducts && Object.keys(matchedProducts).length > 0 && (
            <Box sx={{ mb: 3 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={addToCart}
                    onChange={(e) => setAddToCart(e.target.checked)}
                  />
                }
                label="Add selected products to Kroger cart"
              />
            </Box>
          )}

          {/* Items with matched products */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {items.map(item => (
              <Box key={item.name}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Checkbox
                    checked={!!selectedProductsByItem[item.name]}
                    onChange={() => handleSelectProduct(item.name, selectedProductsByItem[item.name] ? null : {})}
                  />
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    {item.name}
                  </Typography>
                  <Chip
                    label={`${item.quantity} ${item.unit}`}
                    size="small"
                    variant="outlined"
                  />
                </Box>

                {/* Matched products for this item */}
                {krogerEnabled && matchedProducts && matchedProducts[item.name]?.length > 0 ? (
                  <Box sx={{ ml: 4, display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {matchedProducts[item.name].slice(0, 3).map(product => (
                      <Card
                        key={product.product_id}
                        sx={{
                          display: 'flex',
                          cursor: 'pointer',
                          backgroundColor: selectedProductsByItem[item.name]?.product_id === product.product_id ? 'action.selected' : 'background.paper',
                          border: selectedProductsByItem[item.name]?.product_id === product.product_id ? '2px solid' : '1px solid',
                          borderColor: selectedProductsByItem[item.name]?.product_id === product.product_id ? 'primary.main' : 'divider',
                          transition: 'all 0.2s',
                          '&:hover': {
                            backgroundColor: 'action.hover',
                          },
                        }}
                        onClick={() => handleSelectProduct(item.name, product)}
                      >
                        {product.image_url && (
                          <CardMedia
                            component="img"
                            sx={{ width: 60, height: 60 }}
                            image={product.image_url}
                            alt={product.description}
                          />
                        )}
                        <CardContent sx={{ flex: 1, py: 1, px: 2 }}>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {product.description}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {product.brand && `${product.brand} • `}
                            {product.size && product.size}
                          </Typography>
                        </CardContent>
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', p: 1 }}>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontWeight: 'bold', 
                              color: (product.price || product.regular_price) ? 'success.main' : 'text.secondary' 
                            }}
                          >
                            {(product.price || product.regular_price) ? `$${(product.price || product.regular_price).toFixed(2)}` : 'N/A'}
                          </Typography>
                          {product.sale_price && product.regular_price && (
                            <Typography variant="caption" sx={{ textDecoration: 'line-through' }}>
                              ${product.regular_price.toFixed(2)}
                            </Typography>
                          )}
                          <Radio
                            checked={selectedProductsByItem[item.name]?.product_id === product.product_id}
                            onChange={() => handleSelectProduct(item.name, product)}
                            sx={{ mt: 'auto' }}
                          />
                        </Box>
                      </Card>
                    ))}
                  </Box>
                ) : krogerEnabled ? (
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 4, fontStyle: 'italic' }}>
                    No Kroger products found. You can still check off this item.
                  </Typography>
                ) : null}
              </Box>
            ))}
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          color="success"
          startIcon={<ShoppingCartIcon />}
        >
          Mark as Checked {selectedCount > 0 && `& Add ${selectedCount} to Cart`}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
