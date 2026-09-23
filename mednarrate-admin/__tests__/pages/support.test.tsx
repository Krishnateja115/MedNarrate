import { render, screen, fireEvent } from '@testing-library/react';
import SupportQueuePage from '@/app/(protected)/support/page';
import { useQuery } from '@tanstack/react-query';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
}));

describe('SupportQueuePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<SupportQueuePage />);
    expect(screen.getByText('Support Queue')).toBeInTheDocument();
  });

  it('renders support tickets correctly', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        status: 'ok',
        tickets: [
          {
            id: 'ticket-1',
            user_email: 'user@example.com',
            title: 'I need help',
            category: 'Account',
            priority: 'P2 High',
            status: 'New',
            assigned_admin_id: null,
            updated_at: '2023-10-27T10:00:00Z',
          }
        ]
      },
      isLoading: false,
      error: null,
    });

    render(<SupportQueuePage />);
    
    expect(screen.getByText('I need help')).toBeInTheDocument();
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
    expect(screen.getByText('P2 High')).toBeInTheDocument();
  });
});
