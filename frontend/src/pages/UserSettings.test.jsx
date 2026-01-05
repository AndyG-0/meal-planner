import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import UserSettings from './UserSettings';
import { authService } from '../services';

vi.mock('../services', () => ({
  authService: {
    getCurrentUser: vi.fn(),
  },
}));

vi.mock('../store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: { id: 1, username: 'testuser', email: 'test@example.com' },
    setUser: vi.fn(),
  })),
}));

describe('UserSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authService.getCurrentUser.mockResolvedValue({ 
      id: 1, 
      username: 'testuser', 
      email: 'test@example.com' 
    });
  });

  it('should render user settings page', async () => {
    render(
      <BrowserRouter>
        <UserSettings />
      </BrowserRouter>
    );

    expect(screen.getByText(/user settings/i)).toBeTruthy();
  });
});
