import { Typography, Grid, Paper, Box } from '@mui/material'
import { Restaurant, CalendarMonth, ShoppingCart } from '@mui/icons-material'

export default function Dashboard() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              height: 200,
            }}
          >
            <Restaurant sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6">My Recipes</Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Manage your recipe collection
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              height: 200,
            }}
          >
            <CalendarMonth sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6">Meal Calendar</Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Plan your meals for the week
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              height: 200,
            }}
          >
            <ShoppingCart sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6">Grocery Lists</Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Generate shopping lists
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
