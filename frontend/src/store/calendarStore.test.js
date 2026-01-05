import { describe, it, expect, beforeEach } from 'vitest';
import { useCalendarStore } from './calendarStore';

describe('calendarStore', () => {
  beforeEach(() => {
    useCalendarStore.setState({
      calendars: [],
      selectedCalendar: null,
      meals: [],
      loading: false,
      error: null,
    });
  });

  it('should initialize with default state', () => {
    const state = useCalendarStore.getState();
    expect(state.calendars).toEqual([]);
    expect(state.selectedCalendar).toBe(null);
    expect(state.meals).toEqual([]);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
  });

  it('should set calendars', () => {
    const mockCalendars = [
      { id: 1, name: 'Calendar 1' },
      { id: 2, name: 'Calendar 2' },
    ];

    useCalendarStore.getState().setCalendars(mockCalendars);

    const state = useCalendarStore.getState();
    expect(state.calendars).toEqual(mockCalendars);
  });

  it('should set selected calendar', () => {
    const mockCalendar = { id: 1, name: 'Calendar 1' };

    useCalendarStore.getState().setSelectedCalendar(mockCalendar);

    const state = useCalendarStore.getState();
    expect(state.selectedCalendar).toEqual(mockCalendar);
  });

  it('should set meals', () => {
    const mockMeals = [
      { id: 1, recipe_id: 1, date: '2024-01-01' },
      { id: 2, recipe_id: 2, date: '2024-01-02' },
    ];

    useCalendarStore.getState().setMeals(mockMeals);

    const state = useCalendarStore.getState();
    expect(state.meals).toEqual(mockMeals);
  });

  it('should add calendar', () => {
    const initialCalendars = [{ id: 1, name: 'Calendar 1' }];
    const newCalendar = { id: 2, name: 'Calendar 2' };

    useCalendarStore.getState().setCalendars(initialCalendars);
    useCalendarStore.getState().addCalendar(newCalendar);

    const state = useCalendarStore.getState();
    expect(state.calendars).toHaveLength(2);
    expect(state.calendars).toContainEqual(newCalendar);
  });

  it('should add meal', () => {
    const initialMeals = [{ id: 1, recipe_id: 1 }];
    const newMeal = { id: 2, recipe_id: 2 };

    useCalendarStore.getState().setMeals(initialMeals);
    useCalendarStore.getState().addMeal(newMeal);

    const state = useCalendarStore.getState();
    expect(state.meals).toHaveLength(2);
    expect(state.meals).toContainEqual(newMeal);
  });

  it('should remove meal', () => {
    const meals = [
      { id: 1, recipe_id: 1 },
      { id: 2, recipe_id: 2 },
      { id: 3, recipe_id: 3 },
    ];

    useCalendarStore.getState().setMeals(meals);
    useCalendarStore.getState().removeMeal(2);

    const state = useCalendarStore.getState();
    expect(state.meals).toHaveLength(2);
    expect(state.meals.find(m => m.id === 2)).toBeUndefined();
  });

  it('should set loading state', () => {
    useCalendarStore.getState().setLoading(true);
    expect(useCalendarStore.getState().loading).toBe(true);

    useCalendarStore.getState().setLoading(false);
    expect(useCalendarStore.getState().loading).toBe(false);
  });

  it('should set and clear error', () => {
    const errorMessage = 'Test error';
    useCalendarStore.getState().setError(errorMessage);
    expect(useCalendarStore.getState().error).toBe(errorMessage);

    useCalendarStore.getState().clearError();
    expect(useCalendarStore.getState().error).toBe(null);
  });
});
