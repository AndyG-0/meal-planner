import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Divider,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  Collapse,
  Snackbar,
  Tooltip,
  Popover,
  Card,
  CardMedia,
  CardContent,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ShoppingCart,
  Download as DownloadIcon,
  Print as PrintIcon,
  ExpandMore,
  ExpandLess,
  OpenInNew as OpenInNewIcon,
  Search as SearchIcon,
} from '@mui/icons-material'
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { format } from 'date-fns'
import { groceryListService, calendarService, krogerService } from '../services'
import { getErrorMessage } from '../utils/errorHandler'
import KrogerLocationSelector from '../components/KrogerLocationSelector'
import KrogerProductSearch from '../components/KrogerProductSearch'
import InAppKrogerCart from '../components/InAppKrogerCart'
import CheckoutModal from '../components/CheckoutModal'

export default function GroceryList() {
  const [lists, setLists] = useState([])
  const [selectedList, setSelectedList] = useState(null)
  const [calendars, setCalendars] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [openCreate, setOpenCreate] = useState(false)
  const [newListName, setNewListName] = useState('')
  const [selectedCalendarId, setSelectedCalendarId] = useState('')
  const [dateFrom, setDateFrom] = useState(null)
  const [dateTo, setDateTo] = useState(null)
  const [openAddItem, setOpenAddItem] = useState(false)
  const [newItemName, setNewItemName] = useState('')
  const [newItemQuantity, setNewItemQuantity] = useState('')
  const [newItemUnit, setNewItemUnit] = useState('')
  const [newItemCategory, setNewItemCategory] = useState('')
  const [selectedItems, setSelectedItems] = useState([]) // For multi-select
  const [actionValue, setActionValue] = useState('') // For action dropdown

  // Search/Filter state
  const [searchFilter, setSearchFilter] = useState('') // Filter grocery list items
  
  // Checkout/Cart state
  const [openCheckoutModal, setOpenCheckoutModal] = useState(false) // Modal for checking off items
  const [itemsToCheckout, setItemsToCheckout] = useState([]) // Items being checked off from cart
  const [matchedProducts, setMatchedProducts] = useState({}) // Matched products per item

  // Kroger integration state
  const [krogerLocation, setKrogerLocation] = useState(null)
  const [krogerEnabled, setKrogerEnabled] = useState(false)
  const [krogerCartEnabled, setKrogerCartEnabled] = useState(false)
  const [krogerAuthStatus, setKrogerAuthStatus] = useState({ authenticated: false })
  const [showKrogerSection, setShowKrogerSection] = useState(false)
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' })
  const [searchingItem, setSearchingItem] = useState(null) // Item being searched for Kroger products
  const [krogerCart, setKrogerCart] = useState(null) // In-app Kroger cart data

  // Product preview popover state
  const [productPopover, setProductPopover] = useState({ anchorEl: null, item: null })

  useEffect(() => {
    loadLists()
    loadCalendars()
    loadKrogerFeatureToggles()
    loadKrogerLocation()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Load auth status when cart feature is enabled
  useEffect(() => {
    if (krogerCartEnabled) {
      loadKrogerAuthStatus()
    }
  }, [krogerCartEnabled])

  // Auto-expand Kroger section when cart has items or user is authenticated
  useEffect(() => {
    if ((krogerCart && krogerCart.total_items > 0) || krogerAuthStatus.authenticated) {
      setShowKrogerSection(true)
    }
  }, [krogerCart, krogerAuthStatus])

  const loadLists = async () => {
    setLoading(true)
    try {
      const data = await groceryListService.getGroceryLists()
      setLists(data)
      if (data.length > 0 && !selectedList) {
        setSelectedList(data[0])
      }
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to load grocery lists'))
    } finally {
      setLoading(false)
    }
  }

  const loadCalendars = async () => {
    try {
      const data = await calendarService.getCalendars()
      setCalendars(data)
    } catch (err) {
      console.error('Failed to load calendars:', err)
    }
  }

  const loadKrogerFeatureToggles = async () => {
    try {
      const toggles = await krogerService.getFeatureToggles()
      setKrogerEnabled(toggles.kroger_product_search || false)
      setKrogerCartEnabled(toggles.kroger_shopping_cart || false)
    } catch (err) {
      console.error('Failed to load Kroger feature toggles:', err)
    }
  }

  const loadKrogerLocation = async () => {
    try {
      const location = await krogerService.getCurrentLocation()
      if (location) {
        setKrogerLocation(location)
      }
    } catch (err) {
      // Silently fail - user may not have set a location yet
    }
  }

  const loadKrogerAuthStatus = async () => {
    try {
      const status = await krogerService.getAuthStatus()
      setKrogerAuthStatus(status)
    } catch (err) {
      console.error('Failed to load Kroger auth status:', err)
      setKrogerAuthStatus({ authenticated: false })
    }
  }

  const handleLocationChange = (newLocation) => {
    setKrogerLocation(newLocation)
    setSnackbar({
      open: true,
      message: 'Kroger store location updated successfully',
      severity: 'success',
    })
  }

  const handleKrogerAuth = async () => {
    try {
      const data = await krogerService.getAuthorizationUrl()
      if (data.authorization_url) {
        // Store current URL to return to after OAuth
        sessionStorage.setItem('kroger_return_url', window.location.href)
        window.location.href = data.authorization_url
      }
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to start Kroger authorization'))
    }
  }

  // Link products to grocery items in the list
  const linkProductsToGroceryItems = async (products, linkedItemsMap = null) => {
    if (!selectedList || !selectedList.id) return

    try {
      let updatedItems = [...selectedList.items]
      console.log('Before update:', updatedItems.map(i => ({ name: i.name, price: i.kroger_price })))

      // Update items with product information
      updatedItems = updatedItems.map(item => {
        // If we have a specific mapping, use it
        if (linkedItemsMap && linkedItemsMap[item.name]) {
          const product = linkedItemsMap[item.name]
          console.log(`Linking product to ${item.name}:`, {
            product_id: product.product_id,
            price: product.price || product.regular_price,
            name: product.description
          })
          return {
            ...item,
            kroger_product_id: product.product_id,
            kroger_upc: product.upc,
            kroger_price: product.price || product.regular_price,
            kroger_product_name: product.description,
            kroger_image_url: product.image_url,
          }
        }
        return item
      })

      console.log('After update:', updatedItems.map(i => ({ name: i.name, price: i.kroger_price })))

      // Save updated items to backend
      await groceryListService.updateGroceryList(selectedList.id, updatedItems)
      const updatedList = { ...selectedList, items: updatedItems }
      setSelectedList(updatedList)
      setLists(lists.map(l => (l.id === selectedList.id ? updatedList : l)))
      console.log('Grocery list updated successfully')
    } catch (err) {
      console.error('Failed to link products to grocery items:', err)
    }
  }

  const handleAddToCart = async (products, linkedItemsMap = null) => {
    if (!krogerLocation) {
      setError('Please select a Kroger store location first')
      return
    }

    try {
      const items = products.map((product) => ({
        upc: product.upc,
        quantity: 1,
        modality: 'PICKUP', // Default to pickup
      }))

      await krogerService.addToCart(items)
      
      // Link products to grocery items if mapping provided
      if (linkedItemsMap && Object.keys(linkedItemsMap).length > 0) {
        console.log('Linking products to items:', linkedItemsMap)
        await linkProductsToGroceryItems(products, linkedItemsMap)
        // Reload the list to ensure we have the latest data
        await loadLists()
      }

      setSnackbar({
        open: true,
        message: `Added ${products.length} item(s) to your Kroger cart${linkedItemsMap ? ' and linked to grocery items' : ''}`,
        severity: 'success',
      })
    } catch (err) {
      const errorMsg = getErrorMessage(err.response?.data?.detail, 'Failed to add items to cart')
      
      // Check if it's an auth error
      if (err.response?.status === 401 || errorMsg.includes('authorization')) {
        setError('Kroger authorization required. Click "Connect to Kroger" to authorize.')
      } else {
        setError(errorMsg)
      }
    }
  }

  const handleViewCart = async () => {
    try {
      const data = await krogerService.getCartUrl()
      if (data.cart_url) {
        window.open(data.cart_url, '_blank')
      }
    } catch (err) {
      const errorMsg = getErrorMessage(err.response?.data?.detail, 'Failed to get cart URL')
      setSnackbar({
        open: true,
        message: errorMsg,
        severity: 'error',
      })
    }
  }

  // Removed handleCheckout - checkout URLs don't work properly
  // Users can only add to cart via API, not remove items

  const handleKrogerLogout = async () => {
    try {
      const userConfirmed = window.confirm('Are you sure you want to disconnect from Kroger?')
      if (!userConfirmed) return

      await krogerService.logout()
      setKrogerAuthStatus({ authenticated: false })
      setSnackbar({
        open: true,
        message: 'Successfully disconnected from Kroger',
        severity: 'success',
      })
    } catch (err) {
      const errorMsg = getErrorMessage(err.response?.data?.detail, 'Failed to logout from Kroger')
      setSnackbar({
        open: true,
        message: errorMsg,
        severity: 'error',
      })
    }
  }

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false })
  }

  const handleProductPopoverOpen = (event, item) => {
    setProductPopover({ anchorEl: event.currentTarget, item })
    // Clear searching item when opening popover to prevent scroll issues
    setSearchingItem(null)
  }

  const handleProductPopoverClose = () => {
    setProductPopover({ anchorEl: null, item: null })
  }

  const handleSearchItemInKroger = (item) => {
    if (!krogerEnabled || !krogerLocation) {
      setSnackbar({
        open: true,
        message: 'Please select a Kroger location first',
        severity: 'warning',
      })
      return
    }
    
    // Remove "(Menu Item)" from the search query if present
    const searchItem = {
      ...item,
      name: item.name.replace(/\s*\(Menu Item\)\s*/i, '').trim()
    }
    
    // Set the searching item and scroll to Kroger section
    setSearchingItem(searchItem)
    setShowKrogerSection(true)
    
    // Scroll to product search section after the section expands
    setTimeout(() => {
      const productSearchSection = document.getElementById('kroger-product-search')
      if (productSearchSection) {
        productSearchSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 300)
  }

  const handleCreateList = async () => {
    if (!newListName || !selectedCalendarId) return

    try {
      const listData = {
        name: newListName,
        date_from: dateFrom?.toISOString(),
        date_to: dateTo?.toISOString(),
      }
      const newList = await groceryListService.createGroceryList(
        selectedCalendarId,
        listData
      )
      setLists([...lists, newList])
      setSelectedList(newList)
      setOpenCreate(false)
      setNewListName('')
      setSelectedCalendarId('')
      setDateFrom(null)
      setDateTo(null)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to create grocery list'))
    }
  }

  const handleDeleteList = async (listId) => {
    if (window.confirm('Are you sure you want to delete this list?')) {
      try {
        await groceryListService.deleteGroceryList(listId)
        const newLists = lists.filter((l) => l.id !== listId)
        setLists(newLists)
        if (selectedList?.id === listId) {
          setSelectedList(newLists.length > 0 ? newLists[0] : null)
        }
      } catch (err) {
        setError(getErrorMessage(err.response?.data?.detail, 'Failed to delete list'))
      }
    }
  }

  const handleToggleItem = (item) => {
    const itemKey = item.name
    setSelectedItems(prev =>
      prev.includes(itemKey)
        ? prev.filter(i => i !== itemKey)
        : [...prev, itemKey]
    )
  }

  const handleSelectAll = () => {
    if (!selectedList) return
    if (selectedItems.length === selectedList.items.length) {
      setSelectedItems([])
    } else {
      setSelectedItems(selectedList.items.map(item => item.name))
    }
  }

  const handleAction = async () => {
    if (!selectedList || selectedItems.length === 0 || !actionValue) return

    try {
      setLoading(true)
      let updatedItems = [...selectedList.items]

      switch (actionValue) {
        case 'check':
          updatedItems = updatedItems.map(item =>
            selectedItems.includes(item.name) ? { ...item, checked: true } : item
          )
          break
        case 'uncheck':
          updatedItems = updatedItems.map(item =>
            selectedItems.includes(item.name) ? { ...item, checked: false } : item
          )
          break
        case 'delete':
          if (!window.confirm(`Delete ${selectedItems.length} selected item(s)?`)) {
            setLoading(false)
            return
          }
          updatedItems = updatedItems.filter(item => !selectedItems.includes(item.name))
          break
        default:
          break
      }

      await groceryListService.updateGroceryList(selectedList.id, updatedItems)
      const updatedList = { ...selectedList, items: updatedItems }
      setSelectedList(updatedList)
      setLists(lists.map(l => (l.id === selectedList.id ? updatedList : l)))
      setSelectedItems([])
      setActionValue('')
      setError(null)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to perform action'))
    } finally {
      setLoading(false)
    }
  }

  const handleAddItem = () => {
    setNewItemName('')
    setNewItemQuantity('')
    setNewItemUnit('')
    setNewItemCategory('')
    setOpenAddItem(true)
  }

  const handleSaveItem = async () => {
    if (!selectedList || !newItemName || !newItemQuantity || !newItemUnit) return

    try {
      // Add new item
      const updatedItems = [
        ...selectedList.items,
        {
          name: newItemName,
          quantity: parseFloat(newItemQuantity),
          unit: newItemUnit,
          category: newItemCategory || 'Other',
          checked: false,
        },
      ]

      await groceryListService.updateGroceryList(selectedList.id, updatedItems)
      const updatedList = { ...selectedList, items: updatedItems }
      setSelectedList(updatedList)
      setLists(lists.map((l) => (l.id === selectedList.id ? updatedList : l)))
      setOpenAddItem(false)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to save item'))
    }
  }

  const handleDeleteItem = async (itemName) => {
    if (!selectedList) return

    try {
      const updatedItems = selectedList.items.filter((item) => item.name !== itemName)
      await groceryListService.updateGroceryList(selectedList.id, updatedItems)
      const updatedList = { ...selectedList, items: updatedItems }
      setSelectedList(updatedList)
      setLists(lists.map((l) => (l.id === selectedList.id ? updatedList : l)))
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to delete item'))
    }
  }

  const handleExportCSV = async () => {
    if (!selectedList) return
    
    try {
      const blob = await groceryListService.exportCSV(selectedList.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${selectedList.name.replace(/\s+/g, '_')}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to export CSV'))
    }
  }

  const handleExportTXT = async () => {
    if (!selectedList) return
    
    try {
      const blob = await groceryListService.exportTXT(selectedList.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${selectedList.name.replace(/\s+/g, '_')}.txt`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to export TXT'))
    }
  }

  const handlePrint = async () => {
    if (!selectedList) return
    
    try {
      const htmlContent = await groceryListService.getPrintHTML(selectedList.id)
      const blob = new Blob([htmlContent], { type: 'text/html' })
      const url = window.URL.createObjectURL(blob)

      const iframe = document.createElement('iframe')
      iframe.style.position = 'fixed'
      iframe.style.right = '0'
      iframe.style.bottom = '0'
      iframe.style.width = '0'
      iframe.style.height = '0'
      iframe.style.border = '0'
      iframe.src = url

      iframe.onload = () => {
        try {
          iframe.contentWindow?.focus()
          iframe.contentWindow?.print()
        } finally {
          window.URL.revokeObjectURL(url)
          // Remove the iframe after print is triggered
          setTimeout(() => {
            if (iframe.parentNode) {
              iframe.parentNode.removeChild(iframe)
            }
          }, 0)
        }
      }

      document.body.appendChild(iframe)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to open print view'))
    }
  }

  // Handle opening the checkout modal for matching items
  const handleOpenCheckoutModal = async (items) => {
    setItemsToCheckout(items)
    
    // Try to match items to Kroger products if location is available
    if (krogerEnabled && krogerLocation) {
      const products = {}
      for (const item of items) {
        try {
          const data = await krogerService.searchProducts(item.name, krogerLocation.location_id, 0, 3)
          products[item.name] = data.products || []
        } catch (err) {
          console.error(`Failed to search for ${item.name}:`, err)
          products[item.name] = []
        }
      }
      setMatchedProducts(products)
    }
    
    setOpenCheckoutModal(true)
  }

  const handleCloseCheckoutModal = () => {
    setOpenCheckoutModal(false)
    setItemsToCheckout([])
    setMatchedProducts({})
  }

  // Add selected items to cart and mark as checked
  const handleConfirmCheckout = async (selectedProductsByItem) => {
    if (!selectedList) return

    try {
      // Add selected products to Kroger cart if available
      const productsToAdd = Object.values(selectedProductsByItem).filter(Boolean)
      if (productsToAdd.length > 0 && krogerCartEnabled && krogerLocation) {
        await handleAddToCart(productsToAdd, selectedProductsByItem)
      }

      // Mark items as checked and update with product information
      let updatedItems = [...selectedList.items]
      updatedItems = updatedItems.map(item => {
        // If item was in checkout, mark as checked
        const isCheckedOut = itemsToCheckout.some(checkoutItem => checkoutItem.name === item.name)
        if (isCheckedOut) {
          // Also link the product if one was selected
          if (selectedProductsByItem[item.name]) {
            const product = selectedProductsByItem[item.name]
            return {
              ...item,
              checked: true,
              kroger_product_id: product.product_id,
              kroger_upc: product.upc,
              kroger_price: product.price || product.regular_price,
              kroger_product_name: product.description,
              kroger_image_url: product.image_url,
            }
          }
          return { ...item, checked: true }
        }
        return item
      })

      await groceryListService.updateGroceryList(selectedList.id, updatedItems)
      const updatedList = { ...selectedList, items: updatedItems }
      setSelectedList(updatedList)
      setLists(lists.map(l => (l.id === selectedList.id ? updatedList : l)))

      handleCloseCheckoutModal()
      setSnackbar({
        open: true,
        message: `${itemsToCheckout.length} item(s) marked as checked${productsToAdd.length > 0 ? ' and added to cart' : ''}`,
        severity: 'success',
      })
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to checkout items'))
    }
  }

  if (loading && lists.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3} flexWrap="wrap" gap={1}>
          <Typography variant="h4" sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}>Grocery Lists</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenCreate(true)}
            size="small"
          >
            Create List
          </Button>
        </Box>

        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box display="flex" gap={2} flexDirection={{ xs: 'column', md: 'row' }}>
          {/* List selector sidebar */}
          <Paper sx={{ width: { xs: '100%', md: 300 }, p: 2, maxHeight: { xs: 'auto', md: 500 }, overflowY: { xs: 'visible', md: 'auto' } }}>
            <Typography variant="h6" gutterBottom>
              Your Lists
            </Typography>
            <List disablePadding sx={{ display: { xs: 'flex', sm: 'block' }, flexDirection: 'row', gap: { xs: 1, sm: 0 }, flexWrap: 'wrap' }}>
              {lists.map((list) => (
                <ListItem
                  key={list.id}
                  button
                  selected={selectedList?.id === list.id}
                  onClick={() => setSelectedList(list)}
                  sx={{ flex: { xs: '1 1 calc(50% - 0.5rem)', sm: 'auto' } }}
                  secondaryAction={
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteList(list.id)
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  }
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <ShoppingCart />
                  </ListItemIcon>
                  <ListItemText
                    primary={list.name}
                    primaryTypographyProps={{ sx: { fontSize: { xs: '0.875rem', sm: '1rem' } } }}
                    secondary={
                      list.date_from && list.date_to
                        ? `${format(new Date(list.date_from), 'MMM d')} - ${format(
                            new Date(list.date_to),
                            'MMM d'
                          )}`
                        : null
                    }
                    secondaryTypographyProps={{ sx: { fontSize: { xs: '0.75rem', sm: '0.875rem' } } }}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>

          {/* Main content */}
          <Paper sx={{ flex: 1, p: { xs: 2, sm: 3 } }}>
            {selectedList ? (
              <>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h5">
                    {selectedList.name}
                  </Typography>
                  <Box
                    display="flex"
                    gap={1}
                    flexWrap="wrap"
                    sx={{
                      flexDirection: { xs: 'column', sm: 'row' },
                    }}
                  >
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<PrintIcon />}
                      onClick={handlePrint}
                      sx={{
                        flex: { xs: 1, sm: 'auto' },
                        minWidth: { xs: '100%', sm: 'auto' },
                      }}
                    >
                      Print
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={handleExportTXT}
                      sx={{
                        flex: { xs: 1, sm: 'auto' },
                        minWidth: { xs: '100%', sm: 'auto' },
                      }}
                    >
                      Export TXT
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={handleExportCSV}
                      sx={{
                        flex: { xs: 1, sm: 'auto' },
                        minWidth: { xs: '100%', sm: 'auto' },
                      }}
                    >
                      Export CSV
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={handleAddItem}
                      sx={{
                        flex: { xs: 1, sm: 'auto' },
                        minWidth: { xs: '100%', sm: 'auto' },
                      }}
                    >
                      Add Item
                    </Button>
                  </Box>
                </Box>
                {selectedList.date_from && selectedList.date_to && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {format(new Date(selectedList.date_from), 'MMM d, yyyy')} -{' '}
                    {format(new Date(selectedList.date_to), 'MMM d, yyyy')}
                  </Typography>
                )}
                
                {/* Search/Filter and Checkout */}
                {selectedList.items.length > 0 && (
                  <Box
                    display="flex"
                    gap={2}
                    mb={2}
                    flexDirection={{ xs: 'column', sm: 'row' }}
                    alignItems={{ xs: 'stretch', sm: 'center' }}
                  >
                    <TextField
                      placeholder="Search items..."
                      value={searchFilter}
                      onChange={(e) => setSearchFilter(e.target.value)}
                      size="small"
                      fullWidth
                      InputProps={{
                        startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                      sx={{ flex: 1 }}
                    />
                    {krogerCartEnabled && (
                      <Tooltip title="Add items to Kroger cart and mark as checked">
                        <Button
                          variant="contained"
                          color="success"
                          size="small"
                          startIcon={<ShoppingCart />}
                          onClick={() => handleOpenCheckoutModal(selectedList.items.filter(item => !item.checked))}
                          disabled={selectedList.items.filter(item => !item.checked).length === 0}
                        >
                          Checkout
                        </Button>
                      </Tooltip>
                    )}
                  </Box>
                )}
                
                {/* Multi-select Actions */}
                {selectedList.items.length > 0 && (
                  <Box
                    display="flex"
                    gap={2}
                    alignItems={{ xs: 'stretch', sm: 'center' }}
                    mb={2}
                    mt={2}
                    sx={{
                      flexDirection: { xs: 'column', sm: 'row' },
                      flexWrap: { xs: 'wrap', sm: 'nowrap' },
                    }}
                  >
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={handleSelectAll}
                      sx={{
                        flex: { xs: 1, sm: 'auto' },
                        minWidth: { xs: '100%', sm: 'auto' },
                      }}
                    >
                      {selectedItems.length === selectedList.items.length ? 'Deselect All' : 'Select All'}
                    </Button>
                    <FormControl size="small" sx={{ minWidth: { xs: '100%', sm: 150 }, flex: { xs: 1, sm: 'auto' } }}>
                      <InputLabel>Action</InputLabel>
                      <Select
                        value={actionValue}
                        label="Action"
                        onChange={(e) => setActionValue(e.target.value)}
                        disabled={selectedItems.length === 0}
                      >
                        <MenuItem value="check">Mark as Checked</MenuItem>
                        <MenuItem value="uncheck">Mark as Unchecked</MenuItem>
                        <MenuItem value="delete">Delete</MenuItem>
                      </Select>
                    </FormControl>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={handleAction}
                      disabled={selectedItems.length === 0 || !actionValue}
                      sx={{
                        flex: { xs: 1, sm: 'auto' },
                        minWidth: { xs: '100%', sm: 'auto' },
                      }}
                    >
                      Apply to {selectedItems.length} item(s)
                    </Button>
                  </Box>
                )}
                
                <Divider sx={{ my: 2 }} />

                {selectedList.items.length > 0 ? (
                  <List>
                    {selectedList.items
                      .filter(item => !searchFilter.trim() || item.name.toLowerCase().includes(searchFilter.toLowerCase()))
                      .map((item, index) => {
                        // Normalize item name for comparison by removing "(Menu Item)" suffix
                        const normalizedItemName = item.name.replace(/\s*\(Menu Item\)\s*/i, '').trim()
                        const isInCart = krogerCart?.items?.some(cartItem => {
                          const normalizedCartItemName = cartItem.grocery_list_item_name?.replace(/\s*\(Menu Item\)\s*/i, '').trim()
                          return normalizedCartItemName === normalizedItemName
                        })
                        const isCrossedOff = item.checked || isInCart
                        const isMenuItem = item.is_menu_item === true
                        
                        return (
                        <ListItem
                          key={`${item.name}-${index}`}
                          dense
                          sx={{
                            opacity: isCrossedOff ? 0.6 : 1,
                            bgcolor: isMenuItem ? 'info.lighter' : 'transparent',
                            borderLeft: isMenuItem ? '4px solid' : 'none',
                            borderLeftColor: isMenuItem ? 'info.main' : 'transparent',
                            mb: 0.5,
                            borderRadius: isMenuItem ? 1 : 0,
                          }}
                          secondaryAction={
                            <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                              {krogerEnabled && (
                                <Tooltip title="Search in Kroger">
                                  <Button
                                    size="small"
                                    onClick={() => handleSearchItemInKroger(item)}
                                    color="primary"
                                    startIcon={<SearchIcon />}
                                    sx={{ minWidth: 'auto', px: 1 }}
                                  >
                                    Search
                                  </Button>
                                </Tooltip>
                              )}
                              <Tooltip title="Delete item">
                                <IconButton
                                  edge="end"
                                  size="small"
                                  onClick={() => handleDeleteItem(item.name)}
                                  color="error"
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          }
                          >
                            <ListItemIcon>
                              <Checkbox
                                edge="start"
                                checked={selectedItems.includes(item.name)}
                                onChange={() => handleToggleItem(item)}
                                tabIndex={-1}
                                disableRipple
                              />
                            </ListItemIcon>
                            <ListItemText
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <span style={{ 
                                    textDecoration: isCrossedOff ? 'line-through' : 'none'
                                  }}>
                                    {item.name}
                                  </span>
                                  {item.kroger_price ? (
                                    <Typography
                                      component="span"
                                      variant="caption"
                                      sx={{
                                        bgcolor: 'success.light',
                                        color: 'success.dark',
                                        px: 1,
                                        py: 0.25,
                                        borderRadius: 1,
                                        fontWeight: 'bold',
                                        cursor: 'pointer',
                                        textDecoration: 'none',
                                        '&:hover': {
                                          bgcolor: 'success.main',
                                          color: 'white',
                                        },
                                      }}
                                      onMouseEnter={(e) => handleProductPopoverOpen(e, item)}
                                      onMouseLeave={handleProductPopoverClose}
                                      onClick={(e) => handleProductPopoverOpen(e, item)}
                                    >
                                      ${item.kroger_price.toFixed(2)}
                                    </Typography>
                                  ) : (() => {
                                    const normalizedItemName = item.name.replace(/\s*\(Menu Item\)\s*/i, '').trim()
                                    const isItemInCart = krogerCart?.items?.some(cartItem => {
                                      const normalizedCartItemName = cartItem.grocery_list_item_name?.replace(/\s*\(Menu Item\)\s*/i, '').trim()
                                      return normalizedCartItemName === normalizedItemName
                                    })
                                    return isItemInCart ? (
                                      <Typography
                                        component="span"
                                        variant="caption"
                                        sx={{
                                          bgcolor: 'success.light',
                                          color: 'success.contrastText',
                                          px: 1,
                                          py: 0.25,
                                          borderRadius: 1,
                                          fontSize: '0.7rem',
                                          cursor: 'pointer',
                                          textDecoration: 'none',
                                          '&:hover': {
                                            bgcolor: 'success.main',
                                          },
                                        }}
                                        onMouseEnter={(e) => handleProductPopoverOpen(e, item)}
                                        onMouseLeave={handleProductPopoverClose}
                                        onClick={(e) => handleProductPopoverOpen(e, item)}
                                      >
                                        In Cart
                                      </Typography>
                                    ) : null
                                  })()}
                                </Box>
                              }
                              secondary={
                                <span style={{ 
                                  textDecoration: isCrossedOff ? 'line-through' : 'none'
                                }}>
                                  {`${item.quantity} ${item.unit}`}
                                </span>
                              }
                            />
                        </ListItem>
                        )
                      })}
                  </List>
                ) : (
                  <Typography color="text.secondary">
                    No items in this list. Add meals to your calendar and regenerate the
                    list.
                  </Typography>
                )}
              </>
            ) : (
              <Box
                display="flex"
                flexDirection="column"
                alignItems="center"
                justifyContent="center"
                minHeight={300}
              >
                <ShoppingCart sx={{ fontSize: 80, color: 'action.disabled', mb: 2 }} />
                <Typography color="text.secondary">
                  Select a list or create a new one
                </Typography>
              </Box>
            )}

            {/* Kroger Integration Section - Always visible when enabled */}
            {(krogerEnabled || krogerCartEnabled) && (
              <>
                <Divider sx={{ my: 3 }} />
                
                <Box
                  id="kroger-section"
                  display="flex"
                  justifyContent="space-between"
                  alignItems="center"
                  mb={2}
                >
                  <Typography variant="h6">Kroger Integration</Typography>
                  <Button
                    size="small"
                    onClick={() => setShowKrogerSection(!showKrogerSection)}
                    endIcon={showKrogerSection ? <ExpandLess /> : <ExpandMore />}
                  >
                    {showKrogerSection ? 'Hide' : 'Show'}
                  </Button>
                </Box>

                <Collapse in={showKrogerSection}>
                  <Box>
                    {/* Location Selector */}
                    <KrogerLocationSelector
                      currentLocation={krogerLocation}
                      onLocationChange={handleLocationChange}
                    />

                    {/* In-App Cart - Always show if product search is enabled */}
                    {krogerEnabled && (
                      <Box mb={3} mt={2}>
                        <Typography variant="h6" gutterBottom>
                          Shopping Cart
                        </Typography>
                        <InAppKrogerCart
                          onCartChange={(cartData) => {
                            setKrogerCart(cartData)
                          }}
                          listId={selectedList?.id}
                          groceryItems={selectedList?.items}
                          onItemUnlinked={loadLists}
                        />
                        <Alert severity="info" sx={{ mt: 2 }}>
                          <Typography variant="body2">
                            <strong>Note:</strong> Items in this cart can be managed here until you send them to Kroger.
                            Once sent, you&apos;ll need to manage them on Kroger&apos;s website.
                          </Typography>
                        </Alert>
                      </Box>
                    )}

                    {/* Cart Authorization (for sending to Kroger) */}
                    {krogerCartEnabled && (
                      <Box mb={2}>
                        {krogerAuthStatus.authenticated ? (
                          <Alert severity="success">
                            Connected to Kroger
                            {krogerAuthStatus.kroger_email && ` as ${krogerAuthStatus.kroger_email}`}
                            {krogerAuthStatus.expires_at && (
                              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                                Expires: {new Date(krogerAuthStatus.expires_at).toLocaleString()}
                              </Typography>
                            )}
                            <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
                              <Tooltip title="View your Kroger shopping cart on their website">
                                <Button
                                  size="small"
                                  variant="outlined"
                                  startIcon={<ShoppingCart />}
                                  endIcon={<OpenInNewIcon />}
                                  onClick={handleViewCart}
                                >
                                  View Kroger Cart
                                </Button>
                              </Tooltip>
                              <Tooltip title="Disconnect from Kroger">
                                <Button
                                  size="small"
                                  variant="outlined"
                                  color="error"
                                  onClick={handleKrogerLogout}
                                >
                                  Logout
                                </Button>
                              </Tooltip>
                            </Box>
                          </Alert>
                        ) : (
                          <Alert severity="info">
                            To send items to your Kroger cart, you need to connect your Kroger account.
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={handleKrogerAuth}
                              sx={{ ml: 2 }}
                            >
                              Connect to Kroger
                            </Button>
                          </Alert>
                        )}
                      </Box>
                    )}

                    {/* Product Search */}
                    {krogerEnabled && (
                      <Box mt={3} id="kroger-product-search">
                        <Typography variant="h6" gutterBottom>
                          Search Kroger Products
                        </Typography>
                        <KrogerProductSearch
                          key={`product-search-${krogerCart?.total_items || 0}-${selectedList?.id || 'none'}`}
                          groceryItems={selectedList?.items || []}
                          locationId={krogerLocation?.location_id}
                          fulfillmentType="PICKUP"
                          onAddToAppCart={async () => {
                            // Clear searching item and reload list to ensure fresh state
                            setSearchingItem(null)
                            await loadLists()
                          }}
                          disabled={!krogerEnabled}
                          searchingItem={searchingItem}
                          onItemLinked={() => {
                            setSearchingItem(null)
                            loadLists() // Reload to get updated items with prices
                          }}
                          listId={selectedList?.id}
                        />
                      </Box>
                    )}
                  </Box>
                </Collapse>
              </>
            )}
          </Paper>
        </Box>

        {/* Create List Dialog */}
        <Dialog open={openCreate} onClose={() => setOpenCreate(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Create Grocery List</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="List Name"
              value={newListName}
              onChange={(e) => setNewListName(e.target.value)}
              sx={{ mt: 2, mb: 2 }}
            />
            <TextField
              select
              fullWidth
              label="Select Calendar"
              value={selectedCalendarId}
              onChange={(e) => setSelectedCalendarId(e.target.value)}
              sx={{ mb: 2 }}
            >
              {calendars.map((calendar) => (
                <MenuItem key={calendar.id} value={calendar.id}>
                  {calendar.name}
                </MenuItem>
              ))}
            </TextField>
            <DatePicker
              label="Date From"
              value={dateFrom}
              onChange={(date) => setDateFrom(date)}
              renderInput={(params) => <TextField {...params} fullWidth sx={{ mb: 2 }} />}
            />
            <DatePicker
              label="Date To"
              value={dateTo}
              onChange={(date) => setDateTo(date)}
              renderInput={(params) => <TextField {...params} fullWidth />}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenCreate(false)}>Cancel</Button>
            <Button
              onClick={handleCreateList}
              variant="contained"
              disabled={!newListName || !selectedCalendarId}
            >
              Create
            </Button>
          </DialogActions>
        </Dialog>

        {/* Add Item Dialog */}
        <Dialog open={openAddItem} onClose={() => setOpenAddItem(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Add Item</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="Item Name"
              value={newItemName}
              onChange={(e) => setNewItemName(e.target.value)}
              sx={{ mt: 2, mb: 2 }}
            />
            <TextField
              fullWidth
              label="Quantity"
              type="number"
              value={newItemQuantity}
              onChange={(e) => setNewItemQuantity(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Unit"
              value={newItemUnit}
              onChange={(e) => setNewItemUnit(e.target.value)}
              placeholder="e.g., cup, tbsp, oz, g"
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Category (optional)"
              value={newItemCategory}
              onChange={(e) => setNewItemCategory(e.target.value)}
              placeholder="e.g., Produce, Dairy, Meat"
              sx={{ mb: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenAddItem(false)}>Cancel</Button>
            <Button
              onClick={handleSaveItem}
              variant="contained"
              disabled={!newItemName || !newItemQuantity || !newItemUnit}
            >
              Add
            </Button>
          </DialogActions>
        </Dialog>

        {/* Checkout Modal */}
        <CheckoutModal
          open={openCheckoutModal}
          items={itemsToCheckout}
          matchedProducts={matchedProducts}
          krogerEnabled={krogerEnabled}
          krogerCartEnabled={krogerCartEnabled}
          onConfirm={handleConfirmCheckout}
          onClose={handleCloseCheckoutModal}
        />

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert
            onClose={handleCloseSnackbar}
            severity={snackbar.severity}
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>

        {/* Product Preview Popover */}
        <Popover
          open={Boolean(productPopover.anchorEl)}
          anchorEl={productPopover.anchorEl}
          onClose={handleProductPopoverClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'left',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'left',
          }}
          sx={{
            pointerEvents: 'none',
          }}
          slotProps={{
            paper: {
              onMouseEnter: () => setProductPopover((prev) => ({ ...prev })),
              onMouseLeave: handleProductPopoverClose,
              sx: { pointerEvents: 'auto' },
            },
          }}
        >
          {productPopover.item && (() => {
            // Check if item is linked directly or in cart
            const hasDirectLink = productPopover.item.kroger_product_id || productPopover.item.kroger_image_url
            const normalizedItemName = productPopover.item.name.replace(/\s*\(Menu Item\)\s*/i, '').trim()
            const cartItem = krogerCart?.items?.find(ci => {
              const normalizedCartItemName = ci.grocery_list_item_name?.replace(/\s*\(Menu Item\)\s*/i, '').trim()
              return normalizedCartItemName === normalizedItemName
            })
            
            if (!hasDirectLink && !cartItem) return null
            
            // Use direct link data if available, otherwise use cart item data
            const displayData = hasDirectLink ? productPopover.item : {
              kroger_image_url: cartItem?.image_url,
              kroger_product_name: cartItem?.product_name,
              kroger_price: cartItem?.price,
              kroger_upc: cartItem?.upc,
              name: productPopover.item.name,
            }
            
            return (
              <Card sx={{ maxWidth: 300 }}>
                {displayData.kroger_image_url && (
                  <CardMedia
                    component="img"
                    height="200"
                    image={displayData.kroger_image_url}
                    alt={displayData.kroger_product_name || displayData.name}
                    sx={{ objectFit: 'contain', bgcolor: 'grey.100' }}
                  />
                )}
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    {displayData.kroger_product_name || displayData.name}
                  </Typography>
                  {displayData.kroger_price ? (
                    <Typography variant="h6" color="success.main" fontWeight="bold">
                      ${displayData.kroger_price.toFixed(2)}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Price: N/A
                    </Typography>
                  )}
                  {displayData.kroger_upc && (
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                      UPC: {displayData.kroger_upc}
                    </Typography>
                  )}
                  {cartItem && (
                    <Typography variant="caption" color="success.main" display="block" sx={{ mt: 1, fontWeight: 'bold' }}>
                      ✓ In Cart (Qty: {cartItem.quantity})
                    </Typography>
                  )}
                </CardContent>
              </Card>
            )
          })()}
        </Popover>
      </Box>
    </LocalizationProvider>
  )
}

