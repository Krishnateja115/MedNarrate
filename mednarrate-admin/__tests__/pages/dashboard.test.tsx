import { render, screen } from '@testing-library/react';
import OverviewPage from '@/app/(protected)/page';
import { useQuery } from '@tanstack/react-query';

// Mock useQuery
jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
}));

describe('OverviewPage (Command Center)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<OverviewPage />);
    expect(screen.getByText('Loading operational data...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Failed to load'),
    });

    render(<OverviewPage />);
    expect(screen.getByText('Failed to load command center')).toBeInTheDocument();
  });

  it('renders dashboard metrics correctly', () => {
    (useQuery as jest.Mock).mockImplementation(({ queryKey }) => {
      if (queryKey[0] === 'dashboard-summary') {
        return {
          data: {
            status: 'ok',
            timestamp: '2023-10-27T10:00:00Z',
            users: { total_users: 1000, active_users: 500 },
            reports: { reports_today: 150, reports_processing: 10, reports_failed: 2 },
            analysis: { analysis_success_rate: 98.5, analysis_failure_count: 2 },
            support: { open_support_tickets: 5 },
            incidents: { critical_incidents: 0, open_incidents: 1 },
          },
          isLoading: false,
          error: null,
        };
      }
      if (queryKey[0] === 'dashboard-alerts') {
        return {
          data: {
            status: 'ok',
            alerts: [],
          },
          isLoading: false,
          error: null,
        };
      }
      return { data: null, isLoading: false, error: null };
    });

    render(<OverviewPage />);
    
    // Check main title
    expect(screen.getAllByText('Command Center')[0]).toBeInTheDocument();
    
    // Check specific metrics using getByText with numbers as strings
    expect(screen.getByText('1,000')).toBeInTheDocument(); // total users
    expect(screen.getByText('150')).toBeInTheDocument(); // reports today
    expect(screen.getByText('98.5%')).toBeInTheDocument(); // analysis success rate
    
    // Check status
    expect(screen.getByText('Healthy')).toBeInTheDocument();
  });
});
