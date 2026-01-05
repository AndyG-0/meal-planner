import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from './Dashboard';
import { recipeService, calendarService } from '../services';

vi.mock('../services', () => ({
  recipeService: {
    getRecipes: vi.fn(),
  },
  calendarService: {
    getCalendars: vi.fn(),
    getCalendarMeals: vi.fn(),
  },
}));

vi.mock('../store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: { id: 1, username: 'testuser' },
  })),
}));

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    recipeService.getRecipes.mockResolvedValue({ items: [], pagination: {} });
    calendarService.getCalendars.mockResolvedValue([]);
    calendarService.getCalendarMeals.mockResolvedValue([]);
  });

  it('should render dashboard component', async () => {
    const { container } = render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    expect(container).toBeTruthy();
  });
});
