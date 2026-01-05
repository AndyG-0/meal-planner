import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Groups from './Groups';
import { groupService } from '../services';

vi.mock('../services', () => ({
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

describe('Groups', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    groupService.getGroups.mockResolvedValue([]);
  });

  it('should render groups component', async () => {
    const { container } = render(
      <BrowserRouter>
        <Groups />
      </BrowserRouter>
    );

    expect(container).toBeTruthy();
  });
});
