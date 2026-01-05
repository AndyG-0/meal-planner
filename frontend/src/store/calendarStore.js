import { create } from 'zustand'

export const useCalendarStore = create((set) => ({
  calendars: [],
  selectedCalendar: null,
  meals: [],
  loading: false,
  error: null,

  setCalendars: (calendars) => set({ calendars }),
  setSelectedCalendar: (calendar) => set({ selectedCalendar: calendar }),
  setMeals: (meals) => set({ meals }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),

  addCalendar: (calendar) =>
    set((state) => ({ calendars: [...state.calendars, calendar] })),

  addMeal: (meal) =>
    set((state) => ({ meals: [...state.meals, meal] })),

  removeMeal: (mealId) =>
    set((state) => ({
      meals: state.meals.filter((m) => m.id !== mealId),
    })),

  clearError: () => set({ error: null }),
}))
