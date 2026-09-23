import { render, screen } from '@testing-library/react';
import ReportsPage from '@/app/(protected)/reports/page';
import { useQuery } from '@tanstack/react-query';

// Mock useQuery
jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
}));

describe('ReportsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<ReportsPage />);
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });

  it('renders reports table correctly', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        status: 'ok',
        reports: [
          {
            id: 'r1',
            user_id: 'u1',
            user_email: 'test@example.com',
            title: 'Blood Test Results',
            report_type: 'blood',
            processing_status: 'failed',
            uploaded_at: '2023-10-27T10:00:00Z',
          }
        ],
        pagination: { total: 1, limit: 50, offset: 0 }
      },
      isLoading: false,
      error: null,
    });

    render(<ReportsPage />);
    
    // Check specific fields using partial match or precise selectors depending on UI
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('blood')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument(); // Badge
  });
});
