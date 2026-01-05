import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, useThemeMode } from './ThemeContext';
import { useAuthStore } from '../store/authStore';

function TestComponent() {
  const { mode, toggleTheme } = useThemeMode();
  return (
    <div>
      <div data-testid="theme-mode">{mode}</div>
      <button onClick={toggleTheme}>Toggle Theme</button>
    </div>
  );
}

describe('ThemeContext', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null });
  });

  it('should provide light theme by default', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme-mode').textContent).toBe('light');
  });

  it('should toggle theme mode', async () => {
    const user = userEvent.setup();
    
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    expect(screen.getByTestId('theme-mode').textContent).toBe('light');

    await user.click(button);
    await waitFor(() => {
      expect(screen.getByTestId('theme-mode').textContent).toBe('dark');
    });

    await user.click(button);
    await waitFor(() => {
      expect(screen.getByTestId('theme-mode').textContent).toBe('light');
    });
  });

  it('should use user preference if available', () => {
    useAuthStore.setState({
      user: {
        id: 1,
        preferences: {
          theme: 'dark'
        }
      }
    });

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme-mode').textContent).toBe('dark');
  });
});
