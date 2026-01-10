import { create } from 'zustand'

const LAST_ACTIVE_CALENDAR_KEY = 'lastActiveCalendarId'

export const useCalendarStore = create((set) => ({
  calendars: [],
  selectedCalendar: null,
  meals: [],
  loading: false,
  error: null,

  setCalendars: (calendars) => set({ calendars }),
  
  setSelectedCalendar: (calendar) => {
    // Save the selected calendar ID to localStorage
    if (calendar?.id) {
      localStorage.setItem(LAST_ACTIVE_CALENDAR_KEY, calendar.id.toString())
    }
    return set({ selectedCalendar: calendar })
  },

  getLastActiveCalendarId: () => {
    const id = localStorage.getItem(LAST_ACTIVE_CALENDAR_KEY)
    return id ? parseInt(id, 10) : null
  },

  setMeals: (meals) => set({ meals }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),

  addCalendar: (calendar) =>
    set((state) => ({ calendars: [...state.calendars, calendar] })),

  updateCalendar: (updatedCalendar) =>
    set((state) => ({
      calendars: state.calendars.map((c) =>
        c.id === updatedCalendar.id ? updatedCalendar : c
      ),
      selectedCalendar:
        state.selectedCalendar?.id === updatedCalendar.id
          ? updatedCalendar
          : state.selectedCalendar,
    })),

  removeCalendar: (calendarId) =>
    set((state) => ({
      calendars: state.calendars.filter((c) => c.id !== calendarId),
      selectedCalendar:
        state.selectedCalendar?.id === calendarId
          ? null
          : state.selectedCalendar,
    })),

  addMeal: (meal) =>
    set((state) => ({ meals: [...state.meals, meal] })),

  removeMeal: (mealId) =>
    set((state) => ({
      meals: state.meals.filter((m) => m.id !== mealId),
    })),

  clearError: () => set({ error: null }),
}))
