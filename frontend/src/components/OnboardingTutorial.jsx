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
      'Import and export recipes',
      'Organize recipes into collections',
    ],
  },
  {
    title: 'Plan Your Meals',
    content: 'Use the calendar to plan your meals for the week or month.',
    icon: <CalendarMonth />,
    features: [
      'Add recipes to specific dates and meal types',
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
      'Share recipes within groups',
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
      maxWidth="md"
      fullWidth
      aria-labelledby="tutorial-dialog-title"
    >
      <DialogTitle id="tutorial-dialog-title">
        Getting Started
      </DialogTitle>
      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {tutorialSteps.map((step, index) => (
            <Step key={index}>
              <StepLabel>{step.title}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Box sx={{ display: 'inline-flex', fontSize: 60, color: 'primary.main', mb: 2 }}>
            {currentStep.icon}
          </Box>
          <Typography variant="h5" gutterBottom>
            {currentStep.title}
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            {currentStep.content}
          </Typography>
        </Box>

        {currentStep.features && (
          <List>
            {currentStep.features.map((feature, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <Favorite color="primary" />
                </ListItemIcon>
                <ListItemText primary={feature} />
              </ListItem>
            ))}
          </List>
        )}
      </DialogContent>
      <DialogActions sx={{ justifyContent: 'space-between', px: 3, pb: 2 }}>
        <Button onClick={handleSkip} color="inherit">
          Skip Tutorial
        </Button>
        <Box>
          <Button onClick={handleBack} disabled={activeStep === 0} sx={{ mr: 1 }}>
            Back
          </Button>
          <Button onClick={handleNext} variant="contained">
            {activeStep === tutorialSteps.length - 1 ? 'Get Started' : 'Next'}
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
}
