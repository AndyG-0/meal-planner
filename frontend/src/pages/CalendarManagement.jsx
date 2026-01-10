import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { calendarService, groupService } from '../services'
import { useCalendarStore } from '../store/calendarStore'
import { useAuthStore } from '../store/authStore'
import CreateCalendarDialog from '../components/CreateCalendarDialog'
import { getErrorMessage } from '../utils/errorHandler'

const VISIBILITY_OPTIONS = [
  { value: 'private', label: 'Private (Only me)' },
  { value: 'group', label: 'Group (Shared with group)' },
  { value: 'public', label: 'Public (Everyone)' },
]

export default function CalendarManagement() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { setSelectedCalendar } = useCalendarStore()
  
  const [calendars, setCalendars] = useState([])
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Create calendar dialog
  const [openCreateCalendar, setOpenCreateCalendar] = useState(false)
  
  // Pagination
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)
  const [totalCount, setTotalCount] = useState(0)
  
  // Search
  const [searchTerm, setSearchTerm] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  
  // Edit dialog
  const [openEdit, setOpenEdit] = useState(false)
  const [editingCalendar, setEditingCalendar] = useState(null)
  const [editFormData, setEditFormData] = useState({
    name: '',
    visibility: 'private',
    group_id: null,
  })
  
  // Delete dialog
  const [openDelete, setOpenDelete] = useState(false)
  const [deletingCalendar, setDeletingCalendar] = useState(null)

  useEffect(() => {
    loadGroups()
  }, [])

  useEffect(() => {
    loadCalendars()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, rowsPerPage, searchQuery])

  const loadCalendars = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {
        skip: page * rowsPerPage,
        limit: rowsPerPage,
      }
      if (searchQuery) {
        params.search = searchQuery
      }
      const data = await calendarService.getCalendars(params)
      setCalendars(data)
      // Since we don't have total count from backend, estimate it
      setTotalCount(data.length < rowsPerPage ? page * rowsPerPage + data.length : (page + 1) * rowsPerPage + 1)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to load calendars'))
    } finally {
      setLoading(false)
    }
  }

  const loadGroups = async () => {
    try {
      const data = await groupService.getGroups()
      setGroups(data)
    } catch (err) {
      console.error('Failed to load groups:', err)
    }
  }

  const handleSearch = () => {
    setSearchQuery(searchTerm)
    setPage(0)
  }

  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const handleViewCalendar = (calendar) => {
    setSelectedCalendar(calendar)
    navigate('/calendar')
  }

  const handleEditClick = (calendar) => {
    setEditingCalendar(calendar)
    setEditFormData({
      name: calendar.name,
      visibility: calendar.visibility,
      group_id: calendar.group_id,
    })
    setOpenEdit(true)
  }

  const handleEditSave = async () => {
    if (!editingCalendar) return

    try {
      const updated = await calendarService.updateCalendar(editingCalendar.id, editFormData)
      setCalendars(calendars.map(c => c.id === updated.id ? updated : c))
      setOpenEdit(false)
      setEditingCalendar(null)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to update calendar'))
    }
  }

  const handleDeleteClick = (calendar) => {
    setDeletingCalendar(calendar)
    setOpenDelete(true)
  }

  const handleDeleteConfirm = async () => {
    if (!deletingCalendar) return

    try {
      await calendarService.deleteCalendar(deletingCalendar.id)
      setCalendars(calendars.filter(c => c.id !== deletingCalendar.id))
      setOpenDelete(false)
      setDeletingCalendar(null)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to delete calendar'))
    }
  }

  const getVisibilityLabel = (visibility) => {
    const option = VISIBILITY_OPTIONS.find(opt => opt.value === visibility)
    return option ? option.label : visibility
  }

  const getVisibilityColor = (visibility) => {
    switch (visibility) {
      case 'private': return 'default'
      case 'group': return 'primary'
      case 'public': return 'success'
      default: return 'default'
    }
  }

  const handleCalendarCreated = (created) => {
    // Add the new calendar to the list
    setCalendars([created, ...calendars])
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">
          Calendar Management
        </Typography>
        <Button
          variant="contained"
          onClick={() => setOpenCreateCalendar(true)}
        >
          New Calendar
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Search Bar */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          placeholder="Search calendars by name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={handleSearchKeyPress}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
        />
        <Button
          variant="contained"
          onClick={handleSearch}
          sx={{ minWidth: 100 }}
        >
          Search
        </Button>
      </Box>

      {/* Calendar Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Visibility</TableCell>
              <TableCell>Owner</TableCell>
              <TableCell>Access</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : calendars.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No calendars found
                </TableCell>
              </TableRow>
            ) : (
              calendars.map((calendar) => (
                <TableRow key={calendar.id} hover>
                  <TableCell>
                    <Typography variant="body1" fontWeight="medium">
                      {calendar.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getVisibilityLabel(calendar.visibility)}
                      color={getVisibilityColor(calendar.visibility)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {calendar.owner_id === user?.id ? (
                      <Chip label="You" color="primary" size="small" variant="outlined" />
                    ) : (
                      `User ${calendar.owner_id}`
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={calendar.can_edit ? 'Edit' : 'Read Only'}
                      color={calendar.can_edit ? 'success' : 'default'}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => handleViewCalendar(calendar)}
                      title="View Calendar"
                    >
                      <ViewIcon />
                    </IconButton>
                    {calendar.can_edit && (
                      <>
                        <IconButton
                          size="small"
                          onClick={() => handleEditClick(calendar)}
                          title="Edit Calendar"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteClick(calendar)}
                          title="Delete Calendar"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        {calendars.length > 0 && calendars.length >= rowsPerPage && (
          <TablePagination
            component="div"
            count={totalCount}
            page={page}
            onPageChange={(e, newPage) => setPage(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10))
              setPage(0)
            }}
            rowsPerPageOptions={[5, 10, 25, 50]}
          />
        )}
      </TableContainer>

      {/* Edit Dialog */}
      <Dialog open={openEdit} onClose={() => setOpenEdit(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Calendar</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Calendar Name"
            value={editFormData.name}
            onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            select
            label="Visibility"
            value={editFormData.visibility}
            onChange={(e) => setEditFormData({ ...editFormData, visibility: e.target.value })}
            sx={{ mb: 2 }}
          >
            {VISIBILITY_OPTIONS.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>
          {editFormData.visibility === 'group' && (
            <TextField
              fullWidth
              select
              label="Group"
              value={editFormData.group_id || ''}
              onChange={(e) => setEditFormData({ ...editFormData, group_id: e.target.value })}
            >
              <MenuItem value="">
                <em>None</em>
              </MenuItem>
              {groups.map((group) => (
                <MenuItem key={group.id} value={group.id}>
                  {group.name}
                </MenuItem>
              ))}
            </TextField>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEdit(false)}>Cancel</Button>
          <Button onClick={handleEditSave} variant="contained" color="primary">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={openDelete} onClose={() => setOpenDelete(false)}>
        <DialogTitle>Delete Calendar</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete &quot;{deletingCalendar?.name}&quot;? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDelete(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Calendar Dialog */}
      <CreateCalendarDialog
        open={openCreateCalendar}
        onClose={() => setOpenCreateCalendar(false)}
        onCalendarCreated={handleCalendarCreated}
      />
    </Box>
  )
}
