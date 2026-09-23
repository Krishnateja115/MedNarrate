import { render, screen } from '@testing-library/react';
import AIOpsPage from '@/app/(protected)/ai-ops/page';
import { useQuery } from '@tanstack/react-query';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
}));

describe('AIOpsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<AIOpsPage />);
    expect(screen.getByText('AI Operations')).toBeInTheDocument();
  });

  it('renders overview correctly', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        status: 'ok',
        overview: {
          total_requests: 1000,
          success_rate: 95.5,
          failure_rate: 4.5,
          timeout_rate: 0,
          avg_latency_ms: 2500,
          fallback_usage: 12,
          providers: [{ provider: 'openai', requests: 1000 }]
        },
        traces: [],
        failures: []
      },
      isLoading: false,
      error: null,
    });

    render(<AIOpsPage />);
    
    expect(screen.getAllByText('1,000')[0]).toBeInTheDocument(); // total requests
    expect(screen.getByText('95.5%')).toBeInTheDocument(); // success rate
    expect(screen.getByText('2500 ms')).toBeInTheDocument(); // latency
  });
});
