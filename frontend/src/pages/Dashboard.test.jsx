import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from './Dashboard';

vi.mock('../services', () => ({
  recipeService: {
    getRecipes: vi.fn(),
  },
  calendarService: {
    getCalendars: vi.fn(),
    getCalendarMeals: vi.fn(),
  },
  groceryListService: {
    getGroceryList: vi.fn(),
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
