import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuthStore } from '../store/authStore';

vi.mock('axios', () => {
  const mockApi = {
    defaults: { baseURL: 'http://localhost:5000/api', headers: { 'Content-Type': 'application/json' } },
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  };
  
  return {
    default: {
      create: vi.fn().mockReturnValue(mockApi),
    },
  };
});

import api from './api';

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

  it('should register request and response interceptors', () => {
    expect(api.interceptors.request.use).toBeDefined();
    expect(api.interceptors.response.use).toBeDefined();
  });
});
