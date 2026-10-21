import { fireEvent, render, screen } from '@testing-library/react';
import HealthPage from '@/app/(protected)/health/page';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';

// Mock useQuery
jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
}));
jest.mock('@/lib/api', () => ({ fetchApi: jest.fn() }));

describe('HealthPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<HealthPage />);
    expect(screen.getByText('Checking infrastructure status...')).toBeInTheDocument();
  });

  it('renders health data correctly', () => {
    const refetch = jest.fn();
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        status: 'healthy',
        timestamp: '2023-10-27T10:00:00Z',
        services: {
          api: {
            status: 'healthy',
            last_checked: '2023-10-27T10:00:00Z',
            latency_ms: 15,
            error_summary: null
          },
          database: {
            status: 'degraded',
            last_checked: '2023-10-27T10:00:00Z',
            latency_ms: 500,
            error_summary: 'High latency detected'
          },
          scheduler: {
            status: 'disabled',
            last_checked: '2023-10-27T10:00:00Z',
            latency_ms: null,
            error_summary: null
          }
        }
      },
      isLoading: false,
      error: null,
      refetch,
      isFetching: false,
    });

    render(<HealthPage />);
    
    // Check main title
    expect(screen.getAllByText('Service Health')[0]).toBeInTheDocument();
    
    // Check services rendering
    expect(screen.getByText('API Server')).toBeInTheDocument();
    expect(screen.getByText('PostgreSQL Database')).toBeInTheDocument();
    
    // Check error summary
    expect(screen.getByText('High latency detected')).toBeInTheDocument();
    expect(screen.getByText('15.0 ms')).toBeInTheDocument();
    expect(screen.getByText('Not applicable')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Refresh Status' }));
    expect(refetch).toHaveBeenCalledTimes(1);
    const query = (useQuery as jest.Mock).mock.calls[0][0];
    query.queryFn();
    expect(fetchApi).toHaveBeenCalledWith('/api/v1/admin/system/health', { cache: 'no-store' });
  });
});
