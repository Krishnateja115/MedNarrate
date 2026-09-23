import { render, screen } from '@testing-library/react';
import AutomationOpsPage from '@/app/(protected)/automation-ops/page';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
  useMutation: jest.fn(),
  useQueryClient: jest.fn(),
}));

describe('AutomationOpsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useQueryClient as jest.Mock).mockReturnValue({ invalidateQueries: jest.fn() });
    (useMutation as jest.Mock).mockReturnValue({ mutate: jest.fn() });
  });

  it('renders loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<AutomationOpsPage />);
    expect(screen.getByText('Automation Operations')).toBeInTheDocument();
  });

  it('renders notifications correctly', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        status: 'ok',
        notifications: [
          {
            id: 'notif-1',
            user_id: 'user-1',
            title: 'Medication Reminder',
            status: 'failed',
            error_message: 'Device offline',
            sent_at: '2023-10-27T10:00:00Z',
          }
        ],
        schedules: [],
        jobs: []
      },
      isLoading: false,
      error: null,
    });

    render(<AutomationOpsPage />);
    expect(screen.getByText('Medication Reminder')).toBeInTheDocument();
    expect(screen.getByText('Device offline')).toBeInTheDocument();
  });
});
