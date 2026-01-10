import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import { calendarService, groupService } from '../services'
import { getErrorMessage } from '../utils/errorHandler'

const VISIBILITY_OPTIONS = [
  { value: 'private', label: 'Private (Only me)' },
  { value: 'group', label: 'Group (Shared with group)' },
  { value: 'public', label: 'Public (Everyone)' },
]

export default function CreateCalendarDialog({ open, onClose, onCalendarCreated }) {
  const [groups, setGroups] = useState([])
  const [formData, setFormData] = useState({
    name: '',
    visibility: 'private',
    group_id: null,
  })
  const [error, setError] = useState(null)

  useEffect(() => {
    if (open) {
      loadGroups()
      // Reset form when dialog opens
      setFormData({ name: '', visibility: 'private', group_id: null })
      setError(null)
    }
  }, [open])

  const loadGroups = async () => {
    try {
      const data = await groupService.getGroups()
      setGroups(data)
    } catch (err) {
      console.error('Failed to load groups:', err)
    }
  }

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      setError('Calendar name is required')
      return
    }

    try {
      const calendarData = {
        name: formData.name,
        visibility: formData.visibility,
        ...(formData.visibility === 'group' && formData.group_id && { 
          group_id: parseInt(formData.group_id) 
        }),
      }
      const created = await calendarService.createCalendar(calendarData)
      
      // Reset form
      setFormData({ name: '', visibility: 'private', group_id: null })
      setError(null)
      
      // Notify parent component
      if (onCalendarCreated) {
        onCalendarCreated(created)
      }
      
      onClose()
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to create calendar'))
    }
  }

  const handleClose = () => {
    setFormData({ name: '', visibility: 'private', group_id: null })
    setError(null)
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Calendar</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          label="Calendar Name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          margin="normal"
          error={!!error}
          helperText={error}
        />
        <FormControl fullWidth margin="normal">
          <InputLabel>Visibility</InputLabel>
          <Select
            value={formData.visibility}
            label="Visibility"
            onChange={(e) => setFormData({ ...formData, visibility: e.target.value, group_id: null })}
          >
            {VISIBILITY_OPTIONS.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        {formData.visibility === 'group' && (
          <FormControl fullWidth margin="normal">
            <InputLabel>Group</InputLabel>
            <Select
              value={formData.group_id || ''}
              label="Group"
              onChange={(e) => setFormData({ ...formData, group_id: e.target.value })}
            >
              <MenuItem value="">
                <em>Select a group</em>
              </MenuItem>
              {groups.map((group) => (
                <MenuItem key={group.id} value={group.id}>
                  {group.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button onClick={handleCreate} variant="contained">
          Create
        </Button>
      </DialogActions>
    </Dialog>
  )
}
