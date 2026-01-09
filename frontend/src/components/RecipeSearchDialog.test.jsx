import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RecipeSearchDialog from './RecipeSearchDialog';
import { recipeService } from '../services';

vi.mock('../services', () => ({
  recipeService: {
    getRecipes: vi.fn(),
    getAllTags: vi.fn(),
  },
}));

describe('RecipeSearchDialog', () => {
  const mockOnClose = vi.fn();
  const mockOnSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    recipeService.getAllTags.mockResolvedValue({});
    recipeService.getRecipes.mockResolvedValue({ 
      items: [], 
      pagination: { total: 0, page: 1, per_page: 10, pages: 0 } 
    });
  });

  it('should handle empty recipe response from backend', async () => {
    render(
      <RecipeSearchDialog 
        open={true} 
        onClose={mockOnClose} 
        onSelect={mockOnSelect}
      />
    );

    await waitFor(() => {
      expect(recipeService.getRecipes).toHaveBeenCalled();
    });

    expect(screen.getByText(/Start searching to see recipes/i)).toBeTruthy();
  });

  it('should handle paginated recipe response with items', async () => {
    const mockRecipes = [
      { id: 1, title: 'Test Recipe 1', category: 'dinner', difficulty: 'easy' },
      { id: 2, title: 'Test Recipe 2', category: 'lunch', difficulty: 'medium' },
    ];

    recipeService.getRecipes.mockResolvedValue({ 
      items: mockRecipes, 
      pagination: { total: 2, page: 1, per_page: 10, pages: 1 } 
    });

    render(
      <RecipeSearchDialog 
        open={true} 
        onClose={mockOnClose} 
        onSelect={mockOnSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Test Recipe 1')).toBeTruthy();
      expect(screen.getByText('Test Recipe 2')).toBeTruthy();
    });

    expect(screen.getByText(/2 recipes found/i)).toBeTruthy();
  });

  it('should handle backend returning object without items property gracefully', async () => {
    // Simulate a backend error or unexpected response
    recipeService.getRecipes.mockResolvedValue({ 
      items: undefined, 
      pagination: {} 
    });

    render(
      <RecipeSearchDialog 
        open={true} 
        onClose={mockOnClose} 
        onSelect={mockOnSelect}
      />
    );

    await waitFor(() => {
      expect(recipeService.getRecipes).toHaveBeenCalled();
    });

    // Should show empty state instead of crashing
    expect(screen.getByText(/Start searching to see recipes/i)).toBeTruthy();
  });

  it('should allow selecting a recipe', async () => {
    const mockRecipes = [
      { id: 1, title: 'Test Recipe 1', category: 'dinner', difficulty: 'easy' },
    ];

    recipeService.getRecipes.mockResolvedValue({ 
      items: mockRecipes, 
      pagination: { total: 1, page: 1, per_page: 10, pages: 1 } 
    });

    const user = userEvent.setup();

    render(
      <RecipeSearchDialog 
        open={true} 
        onClose={mockOnClose} 
        onSelect={mockOnSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Test Recipe 1')).toBeTruthy();
    });

    // Click the recipe to select it
    await user.click(screen.getByText('Test Recipe 1'));

    // Click the Select button
    const selectButton = screen.getByRole('button', { name: /Select/i });
    expect(selectButton).not.toBeDisabled();
    
    await user.click(selectButton);

    expect(mockOnSelect).toHaveBeenCalledWith(mockRecipes[0]);
    expect(mockOnClose).toHaveBeenCalled();
  });
});
