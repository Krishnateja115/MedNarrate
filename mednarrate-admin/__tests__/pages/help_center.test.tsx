import { render, screen } from '@testing-library/react';
import HelpCenterPage from '@/app/(protected)/help-center/page';
import { useQuery } from '@tanstack/react-query';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
}));

describe('HelpCenterPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<HelpCenterPage />);
    expect(screen.getByText('Help Center')).toBeInTheDocument();
  });

  it('renders articles table correctly', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        status: 'ok',
        articles: [
          {
            id: 'art-1',
            title: 'How to reset password',
            slug: 'how-to-reset-password',
            category: 'Account',
            status: 'published',
            updated_at: '2023-10-27T10:00:00Z',
          }
        ]
      },
      isLoading: false,
      error: null,
    });

    render(<HelpCenterPage />);
    
    expect(screen.getByText('How to reset password')).toBeInTheDocument();
    expect(screen.getByText('how-to-reset-password')).toBeInTheDocument();
    expect(screen.getByText('Published')).toBeInTheDocument();
  });
});
