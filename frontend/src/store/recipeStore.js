import { create } from 'zustand'

export const useRecipeStore = create((set) => ({
  recipes: [],
  selectedRecipe: null,
  loading: false,
  error: null,

  setRecipes: (recipes) => set({ recipes }),
  setSelectedRecipe: (recipe) => set({ selectedRecipe: recipe }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),

  addRecipe: (recipe) =>
    set((state) => ({ recipes: [...state.recipes, recipe] })),

  updateRecipe: (id, updatedRecipe) =>
    set((state) => ({
      recipes: state.recipes.map((r) => (r.id === id ? { ...r, ...updatedRecipe } : r)),
      selectedRecipe: state.selectedRecipe?.id === id ? { ...state.selectedRecipe, ...updatedRecipe } : state.selectedRecipe,
    })),

  deleteRecipe: (id) =>
    set((state) => ({
      recipes: state.recipes.filter((r) => r.id !== id),
      selectedRecipe: state.selectedRecipe?.id === id ? null : state.selectedRecipe,
    })),

  clearError: () => set({ error: null }),
}))
