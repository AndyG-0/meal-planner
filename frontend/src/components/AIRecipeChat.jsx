import { useState, useEffect, useRef } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Chip,
  Card,
  CardContent,
  Grid,
  Divider,
  FormControlLabel,
  Switch,
} from '@mui/material'
import {
  SmartToy as AIIcon,
  Person as PersonIcon,
  Send as SendIcon,
  Check as CheckIcon,
  Close as CloseIcon,
} from '@mui/icons-material'
import api from '../services/api'

export default function AIRecipeChat({ open, onClose, onRecipeCreated }) {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [pendingAction, setPendingAction] = useState(null)
  const [useDietaryPreferences, setUseDietaryPreferences] = useState(true)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (open) {
      // Add initial greeting when chat opens
      setMessages([
        {
          role: 'assistant',
          content: `Hi! I'm your AI cooking assistant. I can help you create amazing recipes! 

Here are some things you can ask me:
• "Create a random recipe"
• "I need a vegan dinner recipe"
• "Create a gluten-free breakfast"
• "Make me a copycat Chipotle burrito bowl"
• "I want a quick 30-minute lunch"
• "Search for healthy dessert ideas" (I can search the web!)
• "Here's a recipe link: [URL]" (I can import recipes from websites!)

What would you like to create today?`,
        },
      ])
      setError('')
      setPendingAction(null)
    }
  }, [open])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading) return

    const userMessage = { role: 'user', content: inputMessage }
    setMessages((prev) => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)
    setError('')

    try {
      const response = await api.post('/ai/chat', {
        messages: [...messages, userMessage],
        use_dietary_preferences: useDietaryPreferences,
      })

      const aiMessage = {
        role: 'assistant',
        content: response.data.message || null,  // Use null if empty
        tool_calls: response.data.tool_calls || undefined  // Include tool_calls if present
      }

      setMessages((prev) => [...prev, aiMessage])

      // Check if there are tool calls (recipe creation/update requests)
      if (response.data.tool_calls && response.data.tool_calls.length > 0) {
        const toolCall = response.data.tool_calls[0]
        
        // Auto-execute search_web and fetch_url tools, send results back to AI
        if (toolCall.name === 'search_web' || toolCall.name === 'fetch_url') {
          try {
            const toolResponse = await api.post('/ai/execute-tool', toolCall)
            
            // Send tool results back to AI in the correct format for OpenAI
            const toolResultMessage = {
              role: 'tool',
              tool_call_id: toolCall.id,
              content: JSON.stringify(toolResponse.data)
            }
            
            const continuedResponse = await api.post('/ai/chat', {
              messages: [...messages, userMessage, aiMessage, toolResultMessage],
              use_dietary_preferences: useDietaryPreferences,
            })
            
            const aiFollowUp = {
              role: 'assistant',
              content: continuedResponse.data.message,
              tool_calls: continuedResponse.data.tool_calls || undefined
            }
            
            // IMPORTANT: Add both the tool result AND the AI follow-up to message history
            setMessages((prev) => [...prev, toolResultMessage, aiFollowUp])
            
            // Check if AI now wants to create a recipe
            if (continuedResponse.data.tool_calls && continuedResponse.data.tool_calls.length > 0) {
              const nextToolCall = continuedResponse.data.tool_calls[0]
              if (nextToolCall.name === 'create_recipe' || nextToolCall.name === 'update_recipe') {
                setPendingAction({
                  tool_call: nextToolCall,
                  recipe_data: nextToolCall.arguments,
                })
              }
            }
          } catch (toolErr) {
            const errorMsg = typeof toolErr.response?.data?.detail === 'string' 
              ? toolErr.response.data.detail 
              : JSON.stringify(toolErr.response?.data?.detail) || 'Failed to execute tool'
            setError(errorMsg)
          }
        } else {
          // For create_recipe and update_recipe, wait for user confirmation
          setPendingAction({
            tool_call: toolCall,
            recipe_data: toolCall.arguments,
          })
        }
      }
    } catch (err) {
      const errorMsg = typeof err.response?.data?.detail === 'string' 
        ? err.response.data.detail 
        : JSON.stringify(err.response?.data?.detail) || 'Failed to communicate with AI'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmAction = async () => {
    if (!pendingAction) return

    setLoading(true)
    setError('')

    try {
      const response = await api.post('/ai/execute-tool', pendingAction.tool_call)

      if (response.data.success) {
        const successMessage = {
          role: 'assistant',
          content: `Great! I've ${
            response.data.action === 'create' ? 'created' : 'updated'
          } the recipe "${pendingAction.recipe_data.name}". You can find it in your recipes!`,
        }

        setMessages((prev) => [...prev, successMessage])
        setPendingAction(null)

        // Notify parent component
        if (onRecipeCreated) {
          onRecipeCreated(response.data.recipe)
        }
      }
    } catch (err) {
      const errorMsg = typeof err.response?.data?.detail === 'string' 
        ? err.response.data.detail 
        : JSON.stringify(err.response?.data?.detail) || 'Failed to execute action'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleCancelAction = () => {
    setPendingAction(null)
    const cancelMessage = {
      role: 'assistant',
      content: 'No problem! Let me know if you want to make any changes, or we can start over with a different recipe.',
    }
    setMessages((prev) => [...prev, cancelMessage])
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const renderRecipePreview = (recipeData) => {
    return (
      <Card sx={{ mt: 2, border: '2px solid #1976d2' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recipe Preview
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
            {recipeData.name}
          </Typography>

          {recipeData.description && (
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              {recipeData.description}
            </Typography>
          )}

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={4}>
              <Typography variant="caption" color="textSecondary">
                Prep Time
              </Typography>
              <Typography variant="body2">{recipeData.prep_time} min</Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="caption" color="textSecondary">
                Cook Time
              </Typography>
              <Typography variant="body2">{recipeData.cook_time} min</Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="caption" color="textSecondary">
                Servings
              </Typography>
              <Typography variant="body2">{recipeData.servings}</Typography>
            </Grid>
          </Grid>

          {recipeData.difficulty && (
            <Box sx={{ mb: 2 }}>
              <Chip label={recipeData.difficulty} size="small" color="primary" />
            </Box>
          )}

          {recipeData.tags && recipeData.tags.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Tags:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {recipeData.tags.map((tag, idx) => (
                  <Chip key={idx} label={tag} size="small" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}

          {recipeData.ingredients && recipeData.ingredients.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Ingredients:
              </Typography>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {recipeData.ingredients.map((ing, idx) => (
                  <li key={idx}>
                    <Typography variant="body2">
                      {typeof ing === 'string' 
                        ? ing 
                        : `${ing.quantity || ''} ${ing.unit || ''} ${ing.name || ''}`.trim()
                      }
                    </Typography>
                  </li>
                ))}
              </ul>
            </Box>
          )}

          {recipeData.instructions && recipeData.instructions.length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Instructions:
              </Typography>
              <ol style={{ margin: 0, paddingLeft: 20 }}>
                {recipeData.instructions.map((step, idx) => (
                  <li key={idx}>
                    <Typography variant="body2">{step}</Typography>
                  </li>
                ))}
              </ol>
            </Box>
          )}

          <Box sx={{ mt: 3, display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              color="error"
              startIcon={<CloseIcon />}
              onClick={handleCancelAction}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              color="success"
              startIcon={<CheckIcon />}
              onClick={handleConfirmAction}
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Confirm & Create Recipe'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    )
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <AIIcon />
            <Typography variant="h6">AI Recipe Assistant</Typography>
          </Box>
          <FormControlLabel
            control={
              <Switch
                checked={useDietaryPreferences}
                onChange={(e) => setUseDietaryPreferences(e.target.checked)}
                size="small"
              />
            }
            label={
              <Typography variant="caption">
                Use Dietary Preferences
              </Typography>
            }
          />
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        <Box sx={{ height: '500px', overflowY: 'auto', mb: 2 }}>
          {messages.map((message, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                mb: 2,
              }}
            >
              <Paper
                sx={{
                  p: 2,
                  maxWidth: '80%',
                  bgcolor: message.role === 'user' ? 'primary.main' : 'grey.200',
                  color: message.role === 'user' ? 'primary.contrastText' : '#000000',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  {message.role === 'user' ? (
                    <PersonIcon fontSize="small" sx={{ color: 'inherit' }} />
                  ) : (
                    <AIIcon fontSize="small" sx={{ color: 'primary.main' }} />
                  )}
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      fontWeight: 'bold',
                      color: 'inherit'
                    }}
                  >
                    {message.role === 'user' ? 'You' : 'AI Assistant'}
                  </Typography>
                </Box>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    whiteSpace: 'pre-wrap',
                    color: 'inherit'
                  }}
                >
                  {message.content}
                </Typography>
              </Paper>
            </Box>
          ))}

          {loading && !pendingAction && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
              <CircularProgress size={24} />
            </Box>
          )}

          {pendingAction && renderRecipePreview(pendingAction.recipe_data)}

          <div ref={messagesEndRef} />
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Type your message..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <Button
            variant="contained"
            onClick={handleSendMessage}
            disabled={loading || !inputMessage.trim()}
            sx={{ minWidth: '64px' }}
          >
            {loading ? <CircularProgress size={24} /> : <SendIcon />}
          </Button>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
