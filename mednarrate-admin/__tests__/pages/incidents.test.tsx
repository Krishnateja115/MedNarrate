import { render, screen } from '@testing-library/react';
import IncidentsPage from '@/app/(protected)/incidents/page';
import { useQuery } from '@tanstack/react-query';

// Mock useQuery
jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
}));

describe('IncidentsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    const { container } = render(<IncidentsPage />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders incidents data correctly', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        status: 'ok',
        items: [
          {
            id: '123',
            title: 'Database connection failed',
            severity: 'SEV-1',
            status: 'open',
            affected_service: 'Database',
            started_at: '2023-10-27T10:00:00Z',
            resolved_at: null,
            summary: 'Primary node down',
            resolution: null
          }
        ],
        total: 1
      },
      isLoading: false,
      error: null,
    });

    render(<IncidentsPage />);
    
    // Check main title
    expect(screen.getAllByText('Incidents')[0]).toBeInTheDocument();
    
    // Check incident rendering
    expect(screen.getByText('Database connection failed')).toBeInTheDocument();
    expect(screen.getByText('SEV-1')).toBeInTheDocument();
    expect(screen.getByText('Open')).toBeInTheDocument();
    expect(screen.getByText('Service: Database')).toBeInTheDocument();
  });
});
