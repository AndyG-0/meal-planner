import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import GroceryList from './GroceryList';
import { groceryListService } from '../services';

vi.mock('../services', () => ({
  groceryListService: {
    getGroceryLists: vi.fn(),
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

describe('GroceryList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    groceryListService.getGroceryLists.mockResolvedValue([]);
  });

  it('should render grocery list component', async () => {
    const { container } = render(
      <BrowserRouter>
        <GroceryList />
      </BrowserRouter>
    );

    expect(container).toBeTruthy();
  });
});
