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
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ShoppingCart,
  Edit as EditIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
} from '@mui/icons-material'
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { format } from 'date-fns'
import { groceryListService, calendarService } from '../services'

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
  const [editingItem, setEditingItem] = useState(null)
  const [selectedItems, setSelectedItems] = useState([]) // For multi-select
  const [actionValue, setActionValue] = useState('') // For action dropdown

  useEffect(() => {
    loadLists()
    loadCalendars()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadLists = async () => {
    setLoading(true)
    try {
      const data = await groceryListService.getGroceryLists()
      setLists(data)
      if (data.length > 0 && !selectedList) {
        setSelectedList(data[0])
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load grocery lists')
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
      setError(err.response?.data?.detail || 'Failed to create grocery list')
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
        setError(err.response?.data?.detail || 'Failed to delete list')
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
      setError(err.response?.data?.detail || 'Failed to perform action')
    } finally {
      setLoading(false)
    }
  }

  const handleAddItem = () => {
    setEditingItem(null)
    setNewItemName('')
    setNewItemQuantity('')
    setNewItemUnit('')
    setNewItemCategory('')
    setOpenAddItem(true)
  }

  const handleEditItem = (item) => {
    setEditingItem(item)
    setNewItemName(item.name)
    setNewItemQuantity(item.quantity.toString())
    setNewItemUnit(item.unit)
    setNewItemCategory(item.category || '')
    setOpenAddItem(true)
  }

  const handleSaveItem = async () => {
    if (!selectedList || !newItemName || !newItemQuantity || !newItemUnit) return

    try {
      let updatedItems
      if (editingItem) {
        // Update existing item
        updatedItems = selectedList.items.map((item) =>
          item.name === editingItem.name
            ? {
                name: newItemName,
                quantity: parseFloat(newItemQuantity),
                unit: newItemUnit,
                category: newItemCategory || 'Other',
                checked: item.checked,
              }
            : item
        )
      } else {
        // Add new item
        updatedItems = [
          ...selectedList.items,
          {
            name: newItemName,
            quantity: parseFloat(newItemQuantity),
            unit: newItemUnit,
            category: newItemCategory || 'Other',
            checked: false,
          },
        ]
      }

      await groceryListService.updateGroceryList(selectedList.id, updatedItems)
      const updatedList = { ...selectedList, items: updatedItems }
      setSelectedList(updatedList)
      setLists(lists.map((l) => (l.id === selectedList.id ? updatedList : l)))
      setOpenAddItem(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save item')
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
      setError(err.response?.data?.detail || 'Failed to export CSV')
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
      setError(err.response?.data?.detail || 'Failed to export TXT')
    }
  }

  const handlePrint = async () => {
    if (!selectedList) return
    
    try {
      const htmlContent = await groceryListService.getPrintHTML(selectedList.id)
      const printWindow = window.open('', '_blank')
      if (printWindow) {
        printWindow.document.write(htmlContent)
        printWindow.document.close()
        // Give the content a moment to load, then trigger print
        setTimeout(() => {
          printWindow.print()
        }, 250)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to open print view')
    }
  }

  // Group items by category
  const groupedItems = selectedList?.items.reduce((acc, item) => {
    const category = item.category || 'Other'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(item)
    return acc
  }, {})

  const categories = groupedItems ? Object.keys(groupedItems).sort() : []

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
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">Grocery Lists</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenCreate(true)}
          >
            Create List
          </Button>
        </Box>

        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box display="flex" gap={2}>
          {/* List selector sidebar */}
          <Paper sx={{ width: 300, p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Your Lists
            </Typography>
            <List>
              {lists.map((list) => (
                <ListItem
                  key={list.id}
                  button
                  selected={selectedList?.id === list.id}
                  onClick={() => setSelectedList(list)}
                  secondaryAction={
                    <IconButton
                      edge="end"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteList(list.id)
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  }
                >
                  <ListItemIcon>
                    <ShoppingCart />
                  </ListItemIcon>
                  <ListItemText
                    primary={list.name}
                    secondary={
                      list.date_from && list.date_to
                        ? `${format(new Date(list.date_from), 'MMM d')} - ${format(
                            new Date(list.date_to),
                            'MMM d'
                          )}`
                        : null
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>

          {/* Main content */}
          <Paper sx={{ flex: 1, p: 3 }}>
            {selectedList ? (
              <>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h5">
                    {selectedList.name}
                  </Typography>
                  <Box display="flex" gap={1}>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<PrintIcon />}
                      onClick={handlePrint}
                    >
                      Print
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={handleExportTXT}
                    >
                      Export TXT
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={handleExportCSV}
                    >
                      Export CSV
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={handleAddItem}
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
                
                {/* Multi-select Actions */}
                {selectedList.items.length > 0 && (
                  <Box display="flex" gap={2} alignItems="center" mb={2} mt={2}>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={handleSelectAll}
                    >
                      {selectedItems.length === selectedList.items.length ? 'Deselect All' : 'Select All'}
                    </Button>
                    <FormControl size="small" sx={{ minWidth: 150 }}>
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
                    >
                      Apply to {selectedItems.length} item(s)
                    </Button>
                  </Box>
                )}
                
                <Divider sx={{ my: 2 }} />

                {categories.length > 0 ? (
                  categories.map((category) => (
                    <Box key={category} mb={3}>
                      <Typography variant="h6" gutterBottom>
                        {category}
                      </Typography>
                      <List>
                        {groupedItems[category].map((item, index) => (
                          <ListItem
                            key={`${item.name}-${index}`}
                            dense
                            sx={{
                              textDecoration: item.checked ? 'line-through' : 'none',
                              opacity: item.checked ? 0.6 : 1,
                            }}
                            secondaryAction={
                              <IconButton
                                edge="end"
                                size="small"
                                onClick={() => handleEditItem(item)}
                              >
                                <EditIcon />
                              </IconButton>
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
                              primary={item.name}
                              secondary={`${item.quantity} ${item.unit}`}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  ))
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

        {/* Add/Edit Item Dialog */}
        <Dialog open={openAddItem} onClose={() => setOpenAddItem(false)} maxWidth="sm" fullWidth>
          <DialogTitle>{editingItem ? 'Edit Item' : 'Add Item'}</DialogTitle>
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
              {editingItem ? 'Update' : 'Add'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  )
}

