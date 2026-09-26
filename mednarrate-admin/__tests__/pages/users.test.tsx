import { render, screen } from '@testing-library/react';
import UsersPage from '@/app/(protected)/users/page';
import { useQuery } from '@tanstack/react-query';

// Mock useQuery
jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
}));

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    can: jest.fn().mockReturnValue(true),
    user: { id: 'test', email: 'test@admin.com', full_name: 'Test Admin', role: 'admin', permissions: ['super_admin'] },
  }),
}));

describe('UsersPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<UsersPage />);
    expect(screen.getByText('Users')).toBeInTheDocument();
  });

  it('renders users table correctly', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        items: [
          {
            id: 'u1',
            email: 'test@example.com',
            full_name: 'Test User',
            role: 'patient',
            preferred_language: 'en',
            is_active: true,
            created_at: '2023-10-27T10:00:00Z',
          }
        ],
        total: 1,
        page: 1,
        limit: 25,
        has_next: false,
        has_previous: false,
      },
      isLoading: false,
      error: null,
    });

    render(<UsersPage />);
    
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('Patient')).toBeInTheDocument(); // Badge
    expect(screen.getByText('Active')).toBeInTheDocument(); // Badge
  });
});
