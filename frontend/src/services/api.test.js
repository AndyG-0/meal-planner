import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import api from './api';
import { useAuthStore } from '../store/authStore';
import axios from 'axios';

vi.mock('axios');

describe('api', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({ token: null });
  });

  it('should be created with correct baseURL', () => {
    expect(api.defaults.baseURL).toBeTruthy();
  });

  it('should have correct default headers', () => {
    expect(api.defaults.headers['Content-Type']).toBe('application/json');
  });

  describe('request interceptor', () => {
    it('should add authorization header when token exists', async () => {
      const mockToken = 'test-token';
      useAuthStore.setState({ token: mockToken });

      const config = {
        headers: {},
      };

      const interceptor = api.interceptors.request.handlers[0];
      if (interceptor && interceptor.fulfilled) {
        const result = await interceptor.fulfilled(config);
        expect(result.headers.Authorization).toBe(`Bearer ${mockToken}`);
      }
    });

    it('should not add authorization header when token does not exist', async () => {
      useAuthStore.setState({ token: null });

      const config = {
        headers: {},
      };

      const interceptor = api.interceptors.request.handlers[0];
      if (interceptor && interceptor.fulfilled) {
        const result = await interceptor.fulfilled(config);
        expect(result.headers.Authorization).toBeUndefined();
      }
    });
  });

  describe('response interceptor', () => {
    let originalLocation;

    beforeEach(() => {
      originalLocation = window.location;
      delete window.location;
      window.location = { href: '' };
    });

    afterEach(() => {
      window.location = originalLocation;
    });

    it('should pass through successful responses', async () => {
      const response = { data: { success: true } };
      const interceptor = api.interceptors.response.handlers[0];
      
      if (interceptor && interceptor.fulfilled) {
        const result = await interceptor.fulfilled(response);
        expect(result).toEqual(response);
      }
    });

    it('should handle 401 errors and logout', async () => {
      const logoutSpy = vi.spyOn(useAuthStore.getState(), 'logout');
      useAuthStore.setState({ 
        isAuthenticated: true, 
        token: 'test-token', 
        user: { id: 1 } 
      });

      const error = {
        response: {
          status: 401,
        },
      };

      const interceptor = api.interceptors.response.handlers[0];
      
      if (interceptor && interceptor.rejected) {
        try {
          await interceptor.rejected(error);
        } catch (e) {
          expect(logoutSpy).toHaveBeenCalled();
          expect(window.location.href).toBe('/login');
        }
      }
    });

    it('should pass through non-401 errors', async () => {
      const error = {
        response: {
          status: 500,
        },
      };

      const interceptor = api.interceptors.response.handlers[0];
      
      if (interceptor && interceptor.rejected) {
        try {
          await interceptor.rejected(error);
        } catch (e) {
          expect(e).toEqual(error);
        }
      }
    });
  });
});
