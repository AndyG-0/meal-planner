import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  CircularProgress,
  Typography,
  Box,
  Alert,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material'
import { ShoppingCart as ShoppingCartIcon } from '@mui/icons-material'
import { krogerService } from '../services'
import { getErrorMessage } from '../utils/errorHandler'

export default function KrogerCartDialog({ open, onClose, onCheckout }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [cartData, setCartData] = useState(null)

  // Auto-load cart when dialog opens
  useEffect(() => {
    if (open && !cartData && !loading) {
      handleLoadCart()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const handleLoadCart = async () => {
    if (cartData) {
      // Already loaded, just return
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data = await krogerService.getCart()
      setCartData(data)
    } catch (err) {
      const errorMsg = getErrorMessage(err.response?.data?.detail, 'Failed to load cart')
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setCartData(null)
    setError(null)
    onClose()
  }

  const handleCheckout = () => {
    handleClose()
    onCheckout?.()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <ShoppingCartIcon />
        Kroger Cart
      </DialogTitle>

      <DialogContent>
        {loading && (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        )}

        {error && !loading && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {cartData && !loading && (
          <Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                Total Items: {cartData.total_quantity || 0}
              </Typography>
              {cartData.estimated_total && (
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                  Estimated Total: ${(cartData.estimated_total / 100).toFixed(2)}
                </Typography>
              )}
            </Box>

            <Divider sx={{ my: 2 }} />

            {cartData.items && cartData.items.length > 0 ? (
              <Box sx={{ overflowX: 'auto' }}>
                <Paper>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                        <TableCell sx={{ fontWeight: 'bold' }}>Item</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                          Quantity
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                          Price
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {cartData.items.map((item, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{item.description || item.upc || 'Item'}</TableCell>
                          <TableCell align="right">{item.quantity || 1}</TableCell>
                          <TableCell align="right">
                            {item.price ? `$${(item.price / 100).toFixed(2)}` : 'N/A'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Paper>
              </Box>
            ) : (
              <Typography variant="body2" color="textSecondary">
                Your cart is empty
              </Typography>
            )}

            {cartData.last_modified && (
              <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 2 }}>
                Last modified: {new Date(cartData.last_modified).toLocaleString()}
              </Typography>
            )}
          </Box>
        )}

        {!loading && !cartData && !error && (
          <Typography variant="body2" color="textSecondary">
            Loading your cart...
          </Typography>
        )}
      </DialogContent>

      <DialogActions>
        {cartData && !loading && (
          <Button onClick={handleCheckout} variant="contained" color="success">
            Proceed to Checkout
          </Button>
        )}
        <Button onClick={handleClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
