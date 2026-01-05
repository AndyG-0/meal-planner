import { describe, it, expect, beforeEach } from 'vitest';
import { useRecipeStore } from './recipeStore';

describe('recipeStore', () => {
  beforeEach(() => {
    useRecipeStore.setState({
      recipes: [],
      selectedRecipe: null,
      loading: false,
      error: null,
    });
  });

  it('should initialize with default state', () => {
    const state = useRecipeStore.getState();
    expect(state.recipes).toEqual([]);
    expect(state.selectedRecipe).toBe(null);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
  });

  it('should set recipes', () => {
    const mockRecipes = [
      { id: 1, name: 'Recipe 1' },
      { id: 2, name: 'Recipe 2' },
    ];

    useRecipeStore.getState().setRecipes(mockRecipes);

    const state = useRecipeStore.getState();
    expect(state.recipes).toEqual(mockRecipes);
  });

  it('should set selected recipe', () => {
    const mockRecipe = { id: 1, name: 'Recipe 1' };

    useRecipeStore.getState().setSelectedRecipe(mockRecipe);

    const state = useRecipeStore.getState();
    expect(state.selectedRecipe).toEqual(mockRecipe);
  });

  it('should add recipe', () => {
    const initialRecipes = [{ id: 1, name: 'Recipe 1' }];
    const newRecipe = { id: 2, name: 'Recipe 2' };

    useRecipeStore.getState().setRecipes(initialRecipes);
    useRecipeStore.getState().addRecipe(newRecipe);

    const state = useRecipeStore.getState();
    expect(state.recipes).toHaveLength(2);
    expect(state.recipes).toContainEqual(newRecipe);
  });

  it('should update recipe', () => {
    const recipes = [
      { id: 1, name: 'Recipe 1', ingredients: [] },
      { id: 2, name: 'Recipe 2', ingredients: [] },
    ];

    useRecipeStore.getState().setRecipes(recipes);
    useRecipeStore.getState().updateRecipe(1, { name: 'Updated Recipe 1' });

    const state = useRecipeStore.getState();
    const updatedRecipe = state.recipes.find(r => r.id === 1);
    expect(updatedRecipe.name).toBe('Updated Recipe 1');
    expect(updatedRecipe.ingredients).toEqual([]);
  });

  it('should update selected recipe when updating recipe', () => {
    const recipe = { id: 1, name: 'Recipe 1', ingredients: [] };

    useRecipeStore.getState().setRecipes([recipe]);
    useRecipeStore.getState().setSelectedRecipe(recipe);
    useRecipeStore.getState().updateRecipe(1, { name: 'Updated Recipe 1' });

    const state = useRecipeStore.getState();
    expect(state.selectedRecipe.name).toBe('Updated Recipe 1');
  });

  it('should not update selected recipe when updating different recipe', () => {
    const recipes = [
      { id: 1, name: 'Recipe 1' },
      { id: 2, name: 'Recipe 2' },
    ];

    useRecipeStore.getState().setRecipes(recipes);
    useRecipeStore.getState().setSelectedRecipe(recipes[0]);
    useRecipeStore.getState().updateRecipe(2, { name: 'Updated Recipe 2' });

    const state = useRecipeStore.getState();
    expect(state.selectedRecipe.name).toBe('Recipe 1');
  });

  it('should delete recipe', () => {
    const recipes = [
      { id: 1, name: 'Recipe 1' },
      { id: 2, name: 'Recipe 2' },
      { id: 3, name: 'Recipe 3' },
    ];

    useRecipeStore.getState().setRecipes(recipes);
    useRecipeStore.getState().deleteRecipe(2);

    const state = useRecipeStore.getState();
    expect(state.recipes).toHaveLength(2);
    expect(state.recipes.find(r => r.id === 2)).toBeUndefined();
  });

  it('should clear selected recipe when deleting it', () => {
    const recipe = { id: 1, name: 'Recipe 1' };

    useRecipeStore.getState().setRecipes([recipe]);
    useRecipeStore.getState().setSelectedRecipe(recipe);
    useRecipeStore.getState().deleteRecipe(1);

    const state = useRecipeStore.getState();
    expect(state.selectedRecipe).toBe(null);
  });

  it('should not clear selected recipe when deleting different recipe', () => {
    const recipes = [
      { id: 1, name: 'Recipe 1' },
      { id: 2, name: 'Recipe 2' },
    ];

    useRecipeStore.getState().setRecipes(recipes);
    useRecipeStore.getState().setSelectedRecipe(recipes[0]);
    useRecipeStore.getState().deleteRecipe(2);

    const state = useRecipeStore.getState();
    expect(state.selectedRecipe).toEqual(recipes[0]);
  });

  it('should set loading state', () => {
    useRecipeStore.getState().setLoading(true);
    expect(useRecipeStore.getState().loading).toBe(true);

    useRecipeStore.getState().setLoading(false);
    expect(useRecipeStore.getState().loading).toBe(false);
  });

  it('should set and clear error', () => {
    const errorMessage = 'Test error';
    useRecipeStore.getState().setError(errorMessage);
    expect(useRecipeStore.getState().error).toBe(errorMessage);

    useRecipeStore.getState().clearError();
    expect(useRecipeStore.getState().error).toBe(null);
  });
});
