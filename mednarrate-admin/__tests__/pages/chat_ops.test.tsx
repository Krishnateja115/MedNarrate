import { render, screen } from '@testing-library/react';
import ChatOpsPage from '@/app/(protected)/chat-ops/page';
import { useQuery } from '@tanstack/react-query';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
}));

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ can: () => true }),
}));

describe('ChatOpsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<ChatOpsPage />);
    expect(screen.getByText('Chat & Safety Operations')).toBeInTheDocument();
  });

  it('renders sessions correctly', () => {
    (useQuery as jest.Mock)
      .mockReturnValueOnce({
        data: {
          items: [
          {
            id: 'sess-1',
            user_id: 'user-1',
            report_id: null,
            title: 'General question',
            created_at: '2023-10-27T10:00:00Z',
          }
          ],
          total: 1,
          page: 1,
          limit: 25,
        },
        isLoading: false,
        error: null,
      })
      .mockReturnValueOnce({
        data: { items: [], total: 0, page: 1, limit: 25 },
        isLoading: false,
        error: null,
      });

    render(<ChatOpsPage />);
    expect(screen.getByText('sess-1')).toBeInTheDocument();
  });
});
