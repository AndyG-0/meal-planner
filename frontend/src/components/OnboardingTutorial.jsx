import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  Typography,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Restaurant,
  CalendarMonth,
  ShoppingCart,
  Group as GroupIcon,
  Favorite,
  Settings as SettingsIcon,
} from '@mui/icons-material';

const tutorialSteps = [
  {
    title: 'Welcome to Meal Planner!',
    content: 'Let\'s take a quick tour of the key features to help you get started.',
    icon: <Restaurant />,
  },
  {
    title: 'Manage Your Recipes',
    content: 'Create, edit, and organize your favorite recipes. You can also use AI to generate new recipe ideas!',
    icon: <Restaurant />,
    features: [
      'Add custom recipes with ingredients and instructions',
      'Rate and review recipes',
      'Mark favorites for quick access',
      'Import and export menu items',
      'Organize menu items into collections',
    ],
  },
  {
    title: 'Plan Your Meals',
    content: 'Use the calendar to plan your meals for the week or month.',
    icon: <CalendarMonth />,
    features: [
      'Add menu items to specific dates and meal types',
      'View your meal plan at a glance',
      'Customize calendar start day (Sunday/Monday)',
      'Export calendar to external apps',
    ],
  },
  {
    title: 'Generate Grocery Lists',
    content: 'Automatically create shopping lists based on your meal plan.',
    icon: <ShoppingCart />,
    features: [
      'Generate lists from calendar selections',
      'Check off items as you shop',
      'Edit and customize your lists',
      'Share lists with household members',
    ],
  },
  {
    title: 'Collaborate with Groups',
    content: 'Share recipes and meal plans with family or roommates.',
    icon: <GroupIcon />,
    features: [
      'Create groups and invite members',
      'Share menu items within groups',
      'Collaborate on meal planning',
      'Set permissions for group members',
    ],
  },
  {
    title: 'Customize Your Experience',
    content: 'Personalize your settings to match your preferences.',
    icon: <SettingsIcon />,
    features: [
      'Set dietary preferences (vegan, keto, etc.)',
      'Configure calorie targets',
      'Choose dark or light theme',
      'Adjust calendar settings',
    ],
  },
];

export default function OnboardingTutorial({ open, onClose }) {
  const [activeStep, setActiveStep] = useState(0);

  const handleNext = () => {
    if (activeStep < tutorialSteps.length - 1) {
      setActiveStep(activeStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    setActiveStep(activeStep - 1);
  };

  const handleComplete = () => {
    // Mark tutorial as completed in localStorage
    localStorage.setItem('tutorialCompleted', 'true');
    onClose();
  };

  const handleSkip = () => {
    localStorage.setItem('tutorialCompleted', 'true');
    onClose();
  };

  const currentStep = tutorialSteps[activeStep];

  return (
    <Dialog
      open={open}
      onClose={handleSkip}
      maxWidth="sm"
      fullWidth
      aria-labelledby="tutorial-dialog-title"
      PaperProps={{
        sx: {
          maxHeight: { xs: '90vh', sm: '90vh' },
          m: { xs: 1, sm: 2 },
        },
      }}
    >
      <DialogTitle id="tutorial-dialog-title" sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
        Getting Started
      </DialogTitle>
      <DialogContent
        sx={{
          maxHeight: { xs: 'calc(90vh - 160px)', sm: 'calc(90vh - 160px)' },
          overflow: 'auto',
          py: { xs: 1.5, sm: 2 },
          px: { xs: 1.5, sm: 2 },
        }}
      >
        <Stepper
          activeStep={activeStep}
          sx={{
            mb: 3,
            '& .MuiStep-root': {
              px: { xs: 0.5, sm: 1 },
            },
            '& .MuiStepLabel-label': {
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
            },
          }}
          variant="scrollable"
          scrollButtons="auto"
        >
          {tutorialSteps.map((step, index) => (
            <Step key={index}>
              <StepLabel>{step.title}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Box
            sx={{
              display: 'inline-flex',
              fontSize: { xs: 40, sm: 60 },
              color: 'primary.main',
              mb: 2,
            }}
          >
            {currentStep.icon}
          </Box>
          <Typography variant="h5" gutterBottom sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
            {currentStep.title}
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            {currentStep.content}
          </Typography>
        </Box>

        {currentStep.features && (
          <List sx={{ py: 0 }}>
            {currentStep.features.map((feature, index) => (
              <ListItem key={index} sx={{ py: { xs: 0.75, sm: 1 }, px: { xs: 1, sm: 2 } }}>
                <ListItemIcon sx={{ minWidth: { xs: 36, sm: 40 } }}>
                  <Favorite color="primary" sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }} />
                </ListItemIcon>
                <ListItemText primary={feature} primaryTypographyProps={{ fontSize: { xs: '0.875rem', sm: '1rem' } }} />
              </ListItem>
            ))}
          </List>
        )}
      </DialogContent>
      <DialogActions
        sx={{
          justifyContent: 'space-between',
          px: { xs: 1.5, sm: 3 },
          py: { xs: 1, sm: 2 },
          gap: 1,
          flexWrap: { xs: 'wrap', sm: 'nowrap' },
        }}
      >
        <Button onClick={handleSkip} color="inherit" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
          Skip Tutorial
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            onClick={handleBack}
            disabled={activeStep === 0}
            sx={{
              mr: { xs: 0.5, sm: 1 },
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              px: { xs: 1, sm: 2 },
            }}
          >
            Back
          </Button>
          <Button
            onClick={handleNext}
            variant="contained"
            sx={{
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              px: { xs: 1.5, sm: 2.5 },
            }}
          >
            {activeStep === tutorialSteps.length - 1 ? 'Get Started' : 'Next'}
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
}
