import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Calendar from './Calendar';
import { calendarService, groupService } from '../services';

vi.mock('../services', () => ({
  calendarService: {
    getCalendars: vi.fn(),
    getCalendarMeals: vi.fn(),
  },
  groupService: {
    getGroups: vi.fn(),
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

vi.mock('../store/calendarStore', () => ({
  useCalendarStore: vi.fn(() => ({
    calendars: [],
    selectedCalendar: null,
    meals: [],
    setCalendars: vi.fn(),
    setSelectedCalendar: vi.fn(),
    setMeals: vi.fn(),
  })),
}));

describe('Calendar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    calendarService.getCalendars.mockResolvedValue([]);
    calendarService.getCalendarMeals.mockResolvedValue([]);
    groupService.getGroups.mockResolvedValue([]);
  });

  it('should render calendar component', async () => {
    const { container } = render(
      <BrowserRouter>
        <Calendar />
      </BrowserRouter>
    );

    expect(container).toBeTruthy();
  });
});
