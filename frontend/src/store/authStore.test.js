import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from './authStore';

describe('authStore', () => {
  beforeEach(() => {
    const store = useAuthStore.getState();
    store.logout();
  });

  it('should initialize with default state', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBe(null);
    expect(state.token).toBe(null);
    expect(state.refreshToken).toBe(null);
    expect(state.isAuthenticated).toBe(false);
  });

  it('should set authentication data', () => {
    const mockUser = { id: 1, username: 'testuser' };
    const mockToken = 'test-token';
    const mockRefreshToken = 'refresh-token';

    useAuthStore.getState().setAuth(mockUser, mockToken, mockRefreshToken);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.token).toBe(mockToken);
    expect(state.refreshToken).toBe(mockRefreshToken);
    expect(state.isAuthenticated).toBe(true);
  });

  it('should update user data', () => {
    const initialUser = { id: 1, username: 'testuser' };
    const updatedUser = { id: 1, username: 'updateduser', email: 'test@example.com' };

    useAuthStore.getState().setAuth(initialUser, 'token', 'refresh');
    useAuthStore.getState().setUser(updatedUser);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(updatedUser);
  });

  it('should logout and clear all data', () => {
    const mockUser = { id: 1, username: 'testuser' };
    useAuthStore.getState().setAuth(mockUser, 'token', 'refresh');

    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBe(null);
    expect(state.token).toBe(null);
    expect(state.refreshToken).toBe(null);
    expect(state.isAuthenticated).toBe(false);
  });
});
