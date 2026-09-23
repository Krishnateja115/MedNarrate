import { render, screen } from '@testing-library/react';
import ChatOpsPage from '@/app/(protected)/chat-ops/page';
import { useQuery } from '@tanstack/react-query';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
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
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        status: 'ok',
        sessions: [
          {
            id: 'sess-1',
            user_id: 'user-1',
            report_id: null,
            title: 'General question',
            created_at: '2023-10-27T10:00:00Z',
          }
        ],
        events: []
      },
      isLoading: false,
      error: null,
    });

    render(<ChatOpsPage />);
    expect(screen.getByText('sess-1')).toBeInTheDocument();
  });
});
