import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Typography,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material'
import { LocationOn, Store } from '@mui/icons-material'
import { krogerService } from '../services'
import { getErrorMessage } from '../utils/errorHandler'

export default function KrogerLocationSelector({ currentLocation, onLocationChange }) {
  const [open, setOpen] = useState(false)
  const [zipCode, setZipCode] = useState('')
  const [locations, setLocations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)

  useEffect(() => {
    if (currentLocation) {
      setSelectedLocation(currentLocation)
    }
  }, [currentLocation])

  const handleSearchLocations = async () => {
    if (!zipCode || zipCode.length < 5) {
      setError('Please enter a valid 5-digit ZIP code')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await krogerService.searchLocations(zipCode, null, null, 25)
      setLocations(data.locations || [])
      if (!data.locations || data.locations.length === 0) {
        setError('No Kroger stores found in this area')
      }
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to search locations'))
    } finally {
      setLoading(false)
    }
  }

  const handleSelectLocation = (location) => {
    // If changing location and user already has a location, show warning
    if (currentLocation && currentLocation.location_id !== location.location_id) {
      setSelectedLocation(location)
      setShowConfirmDialog(true)
    } else {
      confirmLocationChange(location)
    }
  }

  const confirmLocationChange = async (location) => {
    setLoading(true)
    setError(null)
    try {
      const locationData = {
        location_id: location.location_id,
        location_name: location.name,
        location_address: location.address || '',
        location_chain: location.chain || null,
        location_data: {
          city: location.city,
          state: location.state,
          zip_code: location.zip_code,
          phone: location.phone,
          distance: location.distance,
          hours: location.hours,
          departments: location.departments,
        },
      }
      
      const savedLocation = await krogerService.saveLocation(locationData)
      
      // Call parent callback with the saved location data from backend
      if (onLocationChange) {
        onLocationChange(savedLocation)
      }
      
      setOpen(false)
      setShowConfirmDialog(false)
      setLocations([])
      setZipCode('')
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to save location'))
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setOpen(false)
    setLocations([])
    setZipCode('')
    setError(null)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearchLocations()
    }
  }

  return (
    <>
      <Box display="flex" alignItems="center" gap={2} mb={2}>
        {currentLocation ? (
          <Box display="flex" alignItems="center" gap={1} flex={1}>
            <Store color="primary" />
            <Box>
              <Typography variant="body2" fontWeight="bold">
                {currentLocation.location_name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {currentLocation.location_data?.city}, {currentLocation.location_data?.state}{' '}
                {currentLocation.location_data?.zip_code}
              </Typography>
            </Box>
            <Chip
              label="Change Store"
              size="small"
              onClick={() => setOpen(true)}
              sx={{ ml: 'auto' }}
            />
          </Box>
        ) : (
          <Button
            variant="outlined"
            startIcon={<LocationOn />}
            onClick={() => setOpen(true)}
            fullWidth
          >
            Select Kroger Store
          </Button>
        )}
      </Box>

      {/* Location Search Dialog */}
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Select Kroger Store Location</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Box display="flex" gap={1} mb={2}>
            <TextField
              fullWidth
              label="ZIP Code"
              value={zipCode}
              onChange={(e) => setZipCode(e.target.value)}
              onKeyPress={handleKeyPress}
              inputProps={{ maxLength: 5 }}
              disabled={loading}
            />
            <Button
              variant="contained"
              onClick={handleSearchLocations}
              disabled={loading || !zipCode}
            >
              {loading ? <CircularProgress size={24} /> : 'Search'}
            </Button>
          </Box>

          {loading && locations.length === 0 && (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          )}

          {locations.length > 0 && (
            <List sx={{ maxHeight: 400, overflow: 'auto' }}>
              {locations.map((location) => (
                <ListItem key={location.location_id} disablePadding>
                  <ListItemButton onClick={() => handleSelectLocation(location)}>
                    <ListItemText
                      primary={location.name}
                      secondary={
                        <>
                          {location.address && (
                            <>
                              {location.address}
                              <br />
                            </>
                          )}
                          {location.city && location.state && (
                            <>
                              {location.city}, {location.state} {location.zip_code}
                              <br />
                            </>
                          )}
                          {location.distance && <>Distance: {location.distance.toFixed(1)} miles</>}
                        </>
                      }
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Confirm Location Change Dialog */}
      <Dialog open={showConfirmDialog} onClose={() => setShowConfirmDialog(false)}>
        <DialogTitle>Confirm Location Change</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Changing your store location will clear your Kroger shopping cart. This action
            cannot be undone.
          </Alert>
          <Typography>
            Are you sure you want to change your store to{' '}
            <strong>{selectedLocation?.name}</strong>?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowConfirmDialog(false)}>Cancel</Button>
          <Button
            onClick={() => confirmLocationChange(selectedLocation)}
            variant="contained"
            color="warning"
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Confirm Change'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}
