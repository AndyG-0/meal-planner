import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ForgotPassword from './ForgotPassword';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('ForgotPassword', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockResolvedValue({
      data: {
        email_enabled: true,
        admin_email: 'admin@test.com',
      },
    });
  });

  it('should render forgot password form when email is enabled', async () => {
    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeTruthy();
    });
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeTruthy();
  });

  it('should have link back to login', async () => {
    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/back to login/i)).toBeTruthy();
    });
  });
});
