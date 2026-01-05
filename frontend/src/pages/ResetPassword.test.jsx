import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ResetPassword from './ResetPassword';

vi.mock('../services', () => ({
  authService: {
    resetPassword: vi.fn(),
  },
}));

describe('ResetPassword', () => {
  it('should render reset password form', () => {
    render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    );

    const passwordFields = screen.getAllByLabelText(/password/i);
    expect(passwordFields.length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /reset password/i })).toBeTruthy();
  });
});
