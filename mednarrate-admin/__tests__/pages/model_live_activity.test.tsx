import { fireEvent, render, screen, within } from '@testing-library/react';
import { useQuery } from '@tanstack/react-query';
import { ModelLiveActivity } from '@/components/model-live-activity';

jest.mock('@tanstack/react-query', () => ({ useQuery: jest.fn() }));

describe('Live model activity', () => {
  it('shows newly used models and the selected refresh window', () => {
    const refetch = jest.fn();
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        generated_at: '2026-10-20T10:00:00Z', window_hours: 24, total_successful_calls: 3,
        models: [
          { provider: 'gemini', model: 'flash', location: 'hosted', successful_calls: 2,
            avg_latency_ms: 150, last_used: '2026-10-20T10:00:00Z', features: { translation: 2 } },
          { provider: 'ollama', model: 'new-small-model', location: 'local', successful_calls: 1,
            avg_latency_ms: 450, last_used: '2026-10-20T09:00:00Z', features: { analysis: 1 } },
        ],
      },
      isPending: false, isFetching: false, error: null, refetch,
    });
    render(<ModelLiveActivity />);
    const panel = screen.getByTestId('model-live-activity');
    expect(within(panel).getByText('new-small-model')).toBeInTheDocument();
    expect(within(panel).getByText('3')).toBeInTheDocument();
    const queryOptions = (useQuery as jest.Mock).mock.calls[0][0];
    expect(queryOptions.refetchInterval).toBe(15_000);
    fireEvent.click(within(panel).getByRole('button', { name: '7 days' }));
    expect((useQuery as jest.Mock).mock.lastCall?.[0].queryKey).toEqual(['live_model_activity', 168]);
    fireEvent.click(within(panel).getByRole('button', { name: 'Refresh' }));
    expect(refetch).toHaveBeenCalled();
  });

  it('explains an empty window without claiming a benchmark result', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: { generated_at: '2026-10-20T10:00:00Z', window_hours: 24,
        total_successful_calls: 0, models: [] },
      isPending: false, isFetching: false, error: null, refetch: jest.fn(),
    });
    render(<ModelLiveActivity />);
    expect(screen.getByText(/No successful model calls were recorded/)).toBeInTheDocument();
    expect(screen.getByText(/not answer accuracy or clinical quality/)).toBeInTheDocument();
  });
});
