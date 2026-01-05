import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Recipes from './Recipes';
import { recipeService } from '../services';

vi.mock('../services', () => ({
  recipeService: {
    getRecipes: vi.fn(),
    getAllTags: vi.fn(),
    checkFeature: vi.fn(),
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

vi.mock('../store/recipeStore', () => ({
  useRecipeStore: vi.fn(() => ({
    recipes: [],
    setRecipes: vi.fn(),
    loading: false,
    setLoading: vi.fn(),
    clearError: vi.fn(),
  })),
}));

describe('Recipes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    recipeService.getRecipes.mockResolvedValue({ 
      items: [], 
      pagination: { total: 0, page: 1, per_page: 10, pages: 0 } 
    });
    recipeService.getAllTags.mockResolvedValue([]);
    recipeService.checkFeature.mockResolvedValue({ enabled: false });
  });

  it('should render recipes page title', async () => {
    render(
      <BrowserRouter>
        <Recipes />
      </BrowserRouter>
    );

    expect(screen.getByText('Recipes')).toBeTruthy();
  });
});
