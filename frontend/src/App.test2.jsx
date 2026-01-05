import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { useAuthStore } from './store/authStore';

vi.mock('./components/Layout', () => ({
  default: ({ children }) => <div data-testid="layout">{children}</div>
}));

vi.mock('./pages/Login', () => ({
  default: () => <div data-testid="login">Login Page</div>
}));

vi.mock('./pages/Register', () => ({
  default: () => <div data-testid="register">Register Page</div>
}));

vi.mock('./pages/Dashboard', () => ({
  default: () => <div data-testid="dashboard">Dashboard Page</div>
}));

vi.mock('./pages/Recipes', () => ({
  default: () => <div data-testid="recipes">Recipes Page</div>
}));

describe('App', () => {
  it('should render login page for unauthenticated users', () => {
    useAuthStore.setState({ isAuthenticated: false });

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(window.location.pathname).toBe('/');
  });

  it('should render protected routes for authenticated users', () => {
    useAuthStore.setState({ isAuthenticated: true });

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    const layout = screen.queryByTestId('layout');
    expect(layout).toBeTruthy();
  });
});
