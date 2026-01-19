import { useState, useEffect } from 'react'
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Chip,
  Card,
  CardContent,
  CardActions,
  Grid,
  Divider,
  Autocomplete,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Group as GroupIcon,
  Person as PersonIcon,
} from '@mui/icons-material'
import { groupService, authService } from '../services'
import { getErrorMessage } from '../utils/errorHandler'

export default function Groups() {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [createDialog, setCreateDialog] = useState(false)
  const [editDialog, setEditDialog] = useState(false)
  const [viewDialog, setViewDialog] = useState(false)
  const [addMemberDialog, setAddMemberDialog] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')
  const [editingGroup, setEditingGroup] = useState(null)
  const [viewingGroup, setViewingGroup] = useState(null)
  const [groupMembers, setGroupMembers] = useState([])
  const [userSearchResults, setUserSearchResults] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [newMemberRole, setNewMemberRole] = useState('member')

  useEffect(() => {
    loadGroups()
  }, [])

  const loadGroups = async () => {
    try {
      setLoading(true)
      const data = await groupService.getGroups()
      setGroups(data)
      setError('')
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to load groups'))
    } finally {
      setLoading(false)
    }
  }

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) {
      setError('Group name is required')
      return
    }

    try {
      await groupService.createGroup({ name: newGroupName })
      await loadGroups()
      setCreateDialog(false)
      setNewGroupName('')
      setSuccess('Group created successfully')
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to create group'))
    }
  }

  const handleEditGroup = (group) => {
    setEditingGroup({ ...group })
    setEditDialog(true)
  }

  const handleSaveEdit = async () => {
    if (!editingGroup?.name.trim()) {
      setError('Group name is required')
      return
    }

    try {
      await groupService.updateGroup(editingGroup.id, { name: editingGroup.name })
      await loadGroups()
      setEditDialog(false)
      setEditingGroup(null)
      setSuccess('Group updated successfully')
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to update group'))
    }
  }

  const handleDeleteGroup = async (groupId) => {
    if (!window.confirm('Are you sure you want to delete this group?')) {
      return
    }

    try {
      await groupService.deleteGroup(groupId)
      await loadGroups()
      setSuccess('Group deleted successfully')
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to delete group'))
    }
  }

  const handleViewGroup = async (group) => {
    try {
      setViewingGroup(group)
      const members = await groupService.getGroupMembers(group.id)
      setGroupMembers(members)
      setViewDialog(true)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to load group details'))
    }
  }

  const handleRemoveMember = async (memberId) => {
    if (!window.confirm('Are you sure you want to remove this member?')) {
      return
    }

    try {
      await groupService.removeGroupMember(viewingGroup.id, memberId)
      const members = await groupService.getGroupMembers(viewingGroup.id)
      setGroupMembers(members)
      setSuccess('Member removed successfully')
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to remove member'))
    }
  }

  const handleOpenAddMember = (group) => {
    setViewingGroup(group)
    setSelectedUser(null)
    setNewMemberRole('member')
    setAddMemberDialog(true)
  }

  const handleSearchUsers = async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2) {
      setUserSearchResults([])
      return
    }
    
    setSearchLoading(true)
    try {
      const response = await authService.searchUsers(searchQuery)
      setUserSearchResults(response)
    } catch (err) {
      console.error('Failed to search users:', err)
      setUserSearchResults([])
    } finally {
      setSearchLoading(false)
    }
  }

  const handleAddMember = async () => {
    if (!selectedUser || !viewingGroup) return
    
    try {
      await groupService.addGroupMember(viewingGroup.id, {
        user_id: selectedUser.id,
        role: newMemberRole,
        can_edit: newMemberRole === 'admin',
        can_delete: newMemberRole === 'admin'
      })
      setSuccess('Member added successfully')
      setAddMemberDialog(false)
      setSelectedUser(null)
      setNewMemberRole('member')
      
      // Refresh members list
      const members = await groupService.getGroupMembers(viewingGroup.id)
      setGroupMembers(members)
    } catch (err) {
      setError(getErrorMessage(err.response?.data?.detail, 'Failed to add member'))
    }
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography>Loading...</Typography>
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <GroupIcon sx={{ fontSize: 40 }} />
          <Typography variant="h4" component="h1">
            My Groups
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialog(true)}
        >
          Create Group
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess('')} sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      {groups.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <GroupIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No Groups Yet
          </Typography>
          <Typography color="text.secondary" paragraph>
            Create a group to share recipes and meal plans with others
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialog(true)}
          >
            Create Your First Group
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {groups.map((group) => (
            <Grid item xs={12} sm={6} md={4} key={group.id}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <GroupIcon color="primary" />
                      <Typography variant="h6">{group.name}</Typography>
                    </Box>
                  </Box>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <PersonIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      {group.member_count || 0} members
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    Created: {new Date(group.created_at).toLocaleDateString()}
                  </Typography>
                </CardContent>
                <CardActions>
                  <Button size="small" onClick={() => handleViewGroup(group)}>
                    View Details
                  </Button>
                  <Button size="small" onClick={() => handleEditGroup(group)}>
                    Edit
                  </Button>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteGroup(group.id)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Group Dialog */}
      <Dialog open={createDialog} onClose={() => setCreateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Group</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Group Name"
            value={newGroupName}
            onChange={(e) => setNewGroupName(e.target.value)}
            margin="normal"
            helperText="Choose a name that describes the purpose of this group"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateGroup} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Group Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Group</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Group Name"
            value={editingGroup?.name || ''}
            onChange={(e) => setEditingGroup({ ...editingGroup, name: e.target.value })}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Group Dialog */}
      <Dialog
        open={viewDialog}
        onClose={() => setViewDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <GroupIcon />
            {viewingGroup?.name}
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box mb={3}>
            <Typography variant="subtitle2" gutterBottom>
              Group Information
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Created: {viewingGroup && new Date(viewingGroup.created_at).toLocaleString()}
            </Typography>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle2">
                Members ({groupMembers.length})
              </Typography>
              <Button
                size="small"
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={() => handleOpenAddMember(viewingGroup)}
              >
                Add Member
              </Button>
            </Box>

            {groupMembers.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No members yet
              </Typography>
            ) : (
              <List>
                {groupMembers.map((member) => (
                  <ListItem key={member.id}>
                    <ListItemText
                      primary={member.user?.username || `User #${member.user_id}`}
                      secondary={
                        <Box>
                          <Chip label={member.role} size="small" sx={{ mr: 1 }} />
                          {member.user?.email && (
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                              {member.user.email}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => handleRemoveMember(member.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Add Member Dialog */}
      <Dialog
        open={addMemberDialog}
        onClose={() => {
          setAddMemberDialog(false)
          setSelectedUser(null)
          setNewMemberRole('member')
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Member to {viewingGroup?.name}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Autocomplete
              fullWidth
              options={userSearchResults || []}
              getOptionLabel={(option) => `${option.username} (${option.email})`}
              value={selectedUser}
              onChange={(event, newValue) => setSelectedUser(newValue)}
              onInputChange={(event, newInputValue) => {
                handleSearchUsers(newInputValue)
              }}
              loading={searchLoading}
              filterOptions={(x) => x}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Search for user"
                  helperText="Type at least 2 characters to search"
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {searchLoading ? <CircularProgress color="inherit" size={20} /> : null}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
            />

            <FormControl fullWidth sx={{ mt: 3 }}>
              <InputLabel>Role</InputLabel>
              <Select
                value={newMemberRole}
                onChange={(e) => setNewMemberRole(e.target.value)}
                label="Role"
              >
                <MenuItem value="member">Member</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
              </Select>
            </FormControl>

            {newMemberRole === 'admin' && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Admins can edit and delete group content
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setAddMemberDialog(false)
            setSelectedUser(null)
            setNewMemberRole('member')
          }}>
            Cancel
          </Button>
          <Button
            onClick={handleAddMember}
            variant="contained"
            disabled={!selectedUser}
          >
            Add Member
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}
