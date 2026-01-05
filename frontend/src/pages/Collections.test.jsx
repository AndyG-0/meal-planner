import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Collections from './Collections';
import { collectionService } from '../services';

vi.mock('../services', () => ({
  collectionService: {
    getCollections: vi.fn(),
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

describe('Collections', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    collectionService.getCollections.mockResolvedValue([]);
  });

  it('should render collections component', async () => {
    const { container } = render(
      <BrowserRouter>
        <Collections />
      </BrowserRouter>
    );

    expect(container).toBeTruthy();
  });
});
