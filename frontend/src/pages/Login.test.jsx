import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from './Login';
import { authService } from '../services';

vi.mock('../services', () => ({
  authService: {
    login: vi.fn(),
  },
}));

vi.mock('../store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    setAuth: vi.fn(),
  })),
}));

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render login form', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    expect(screen.getByLabelText(/username/i)).toBeTruthy();
    expect(screen.getByLabelText(/password/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeTruthy();
  });

  it('should have links to register and forgot password', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    expect(screen.getByText(/don't have an account/i)).toBeTruthy();
    expect(screen.getByText(/forgot your password/i)).toBeTruthy();
  });
});
