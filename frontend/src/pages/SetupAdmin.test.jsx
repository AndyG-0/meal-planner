import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import SetupAdmin from './SetupAdmin';

const mockNavigate = vi.fn();
const mockSetAuth = vi.fn();
const mockMarkSetupComplete = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../services', () => ({
  authService: {
    checkSetupRequired: vi.fn(),
    setupAdmin: vi.fn(),
    login: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

vi.mock('../store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    setAuth: mockSetAuth,
  })),
}));

vi.mock('../store/setupStore', () => ({
  useSetupStore: vi.fn(() => ({
    markSetupComplete: mockMarkSetupComplete,
  })),
}));

describe('SetupAdmin', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render setup form when setup is required', async () => {
    const { authService } = await import('../services');
    authService.checkSetupRequired.mockResolvedValue({ setup_required: true });

    render(
      <BrowserRouter>
        <SetupAdmin />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/initial setup/i)).toBeTruthy();
    });

    expect(screen.getByLabelText(/username/i)).toBeTruthy();
    expect(screen.getByLabelText(/email/i)).toBeTruthy();
    expect(screen.getAllByLabelText(/password/i).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /create admin account/i })).toBeTruthy();
  });

  it('should redirect to login if setup is not required', async () => {
    const { authService } = await import('../services');
    authService.checkSetupRequired.mockResolvedValue({ setup_required: false });

    render(
      <BrowserRouter>
        <SetupAdmin />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
    });
  });

  it('should redirect to login on verification error', async () => {
    const { authService } = await import('../services');
    authService.checkSetupRequired.mockRejectedValue(new Error('Network error'));

    render(
      <BrowserRouter>
        <SetupAdmin />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
    });
  });

  it('should show loading spinner during verification', async () => {
    const { authService } = await import('../services');
    authService.checkSetupRequired.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <BrowserRouter>
        <SetupAdmin />
      </BrowserRouter>
    );

    // Should show loading spinner initially
    const spinner = document.querySelector('.MuiCircularProgress-root');
    expect(spinner).toBeTruthy();
  });
});
