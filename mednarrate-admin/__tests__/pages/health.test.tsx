import { render, screen } from '@testing-library/react';
import HealthPage from '@/app/(protected)/health/page';
import { useQuery } from '@tanstack/react-query';

// Mock useQuery
jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
}));

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
          }
        }
      },
      isLoading: false,
      error: null,
    });

    render(<HealthPage />);
    
    // Check main title
    expect(screen.getAllByText('Service Health')[0]).toBeInTheDocument();
    
    // Check services rendering
    expect(screen.getByText('API Server')).toBeInTheDocument();
    expect(screen.getByText('PostgreSQL Database')).toBeInTheDocument();
    
    // Check error summary
    expect(screen.getByText('High latency detected')).toBeInTheDocument();
  });
});
