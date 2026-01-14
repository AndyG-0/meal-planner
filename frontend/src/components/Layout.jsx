import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import {
  AppBar,
  Box,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Restaurant,
  CalendarMonth,
  ShoppingCart,
  Dashboard as DashboardIcon,
  AdminPanelSettings,
  AccountCircle,
  Group as GroupIcon,
  Settings as SettingsIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Folder as FolderIcon,
  CalendarToday as CalendarTodayIcon,
} from '@mui/icons-material'
import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { useThemeMode } from '../contexts/ThemeContext'

const drawerWidth = 240

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { logout, user } = useAuthStore()
  const { mode, toggleTheme } = useThemeMode()

  // Close mobile drawer when location changes
  useEffect(() => {
    setMobileOpen(false)
  }, [location])

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Menu Items', icon: <Restaurant />, path: '/recipes' },
    { text: 'Collections', icon: <FolderIcon />, path: '/collections' },
    { text: 'Calendar', icon: <CalendarMonth />, path: '/calendar' },
    { text: 'Calendar Management', icon: <CalendarTodayIcon />, path: '/calendar-management' },
    { text: 'Grocery List', icon: <ShoppingCart />, path: '/grocery-lists' },
    { text: 'Groups', icon: <GroupIcon />, path: '/groups' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ]

  // Add admin menu item if user is admin
  if (user?.is_admin) {
    menuItems.push({ text: 'Admin', icon: <AdminPanelSettings />, path: '/admin' })
  }

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Meal Planner
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton component={Link} to={item.path}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </div>
  )

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar sx={{ gap: { xs: 1, sm: 2 }, minHeight: { xs: 56, sm: 64 } }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: { xs: 0, sm: 2 }, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
            Meal Planner
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0.5, sm: 2 } }}>
            <IconButton color="inherit" onClick={toggleTheme} title={`Switch to ${mode === 'light' ? 'dark' : 'light'} mode`} size="small">
              {mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
            </IconButton>
            <Box sx={{ display: { xs: 'none', sm: 'flex' }, alignItems: 'center', gap: 1 }}>
              <AccountCircle />
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                <Typography variant="body2" sx={{ lineHeight: 1.2, fontWeight: 500 }}>
                  {user?.username}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.7)', lineHeight: 1.2 }}>
                  {user?.email}
                  {user?.is_admin && ' • Admin'}
                </Typography>
              </Box>
            </Box>
            <Button color="inherit" onClick={handleLogout} size="small">
              Logout
            </Button>
          </Box>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 1.5, sm: 2, md: 3 },
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          overflow: 'auto',
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  )
}
