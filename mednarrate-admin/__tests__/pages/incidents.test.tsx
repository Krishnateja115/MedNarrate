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

    render(<IncidentsPage />);
    expect(screen.getByText('Loading incident history...')).toBeInTheDocument();
  });

  it('renders incidents data correctly', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        status: 'ok',
        incidents: [
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
        pagination: { limit: 50, offset: 0 }
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
