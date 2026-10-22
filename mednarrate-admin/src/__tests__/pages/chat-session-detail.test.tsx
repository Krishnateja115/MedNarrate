import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApiError, fetchApi } from '@/lib/api';
import ChatSessionDetailPage from '@/app/(protected)/chat-ops/detail/page';

jest.mock('@/lib/api', () => {
  const actual = jest.requireActual('@/lib/api');
  return { ...actual, fetchApi: jest.fn() };
});
jest.mock('next/navigation', () => ({ useSearchParams: () => new URLSearchParams('id=session-123') }));
jest.mock('@/contexts/AuthContext', () => ({ useAuth: () => ({ can: (permission: string) => permission !== 'chat.sensitive_view' || sensitiveAllowed }) }));
jest.mock('@/components/ui/forbidden', () => ({ Forbidden: () => <p>Forbidden</p> }));

let sensitiveAllowed = false;
const mockedFetchApi = jest.mocked(fetchApi);
const detail = {
  session: { id: 'session-123', user_id: 'user-123', report_id: null, created_at: '2026-10-21T10:00:00Z', message_count: 2, sensitive_content_available: true },
  safety_events: [{ id: 'event-1', classification: 'FLAGGED', action_taken: 'REVIEWED', safe_summary: 'Redacted safety summary', created_at: '2026-10-21T10:01:00Z' }],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><ChatSessionDetailPage /></QueryClientProvider>);
}

describe('ChatSessionDetailPage', () => {
  beforeEach(() => {
    sensitiveAllowed = false;
    mockedFetchApi.mockReset();
    mockedFetchApi.mockResolvedValue(detail);
  });

  it('shows safe metadata and summaries without fetching private messages', async () => {
    renderPage();
    expect(await screen.findByText('Redacted safety summary')).toBeInTheDocument();
    expect(screen.getByText('Session metadata')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'View private messages' })).not.toBeInTheDocument();
    expect(mockedFetchApi).toHaveBeenCalledTimes(1);
    expect(mockedFetchApi).toHaveBeenCalledWith('/api/v1/admin/chat-ops/sessions/session-123');
  });

  it('requests private messages only after an explicit click and explains a missing grant', async () => {
    sensitiveAllowed = true;
    mockedFetchApi.mockResolvedValueOnce(detail).mockRejectedValueOnce(new ApiError(403, 'No active grant'));
    renderPage();
    const button = await screen.findByRole('button', { name: 'View private messages' });
    expect(mockedFetchApi).toHaveBeenCalledTimes(1);
    fireEvent.click(button);
    await waitFor(() => expect(mockedFetchApi).toHaveBeenCalledWith('/api/v1/admin/chat-ops/sessions/session-123/messages'));
    expect(await screen.findByText(/active break-glass grant/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Request break-glass access' })).toHaveAttribute('href', '/breakglass?resource_type=chat_session&resource_id=session-123');
  });
});
