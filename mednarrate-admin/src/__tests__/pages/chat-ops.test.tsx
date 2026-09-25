/**
 * Regression tests for chat-ops/page.tsx
 *
 * Specifically guards against:
 * - undefined.map() crash when backend returns {items:[]} instead of {sessions:[]}
 * - Safe rendering under: empty, loading, API error, pagination
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import ChatOpsPage from '@/app/(protected)/chat-ops/page';

// ─── mocks ───────────────────────────────────────────────────────────────────
jest.mock('@/lib/api', () => ({ fetchApi: jest.fn() }));
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    can: () => true,
    hasAnyPermission: () => true,
  }),
}));
jest.mock('@/components/ui/forbidden', () => ({
  Forbidden: () => <div data-testid="forbidden">Forbidden</div>,
}));
jest.mock('@/components/ui/data-table', () => ({
  DataTable: ({ data, isLoading }: { data: unknown[]; isLoading?: boolean }) => (
    <div data-testid="data-table">
      {isLoading ? (
        <div data-testid="loading">loading</div>
      ) : (
        <ul>
          {(data as Array<{ id: string }>).map((row, i) => (
            <li key={i} data-testid="table-row">{row.id}</li>
          ))}
        </ul>
      )}
    </div>
  ),
}));

// Typed mock reference
const mockedFetchApi = jest.mocked(fetchApi);

// ─── helpers ─────────────────────────────────────────────────────────────────
const makeClient = () =>
  new QueryClient({ defaultOptions: { queries: { retry: false } } });

const renderPage = () =>
  render(
    <QueryClientProvider client={makeClient()}>
      <ChatOpsPage />
    </QueryClientProvider>
  );

// ─── build_pagination_response shape ─────────────────────────────────────────
const paginatedSessions = {
  items: [
    { id: 'sess-1111', user_id: 'user-aaaa', report_id: null, title: 'Test Session', created_at: '2026-09-01T10:00:00Z' },
    { id: 'sess-2222', user_id: 'user-bbbb', report_id: 'rep-cccc', title: null, created_at: '2026-09-02T11:00:00Z' },
  ],
  total: 2,
  page: 1,
  limit: 25,
};

// ─── tests ────────────────────────────────────────────────────────────────────
describe('ChatOpsPage', () => {
  beforeEach(() => {
    mockedFetchApi.mockReset();
    mockedFetchApi.mockResolvedValue(paginatedSessions);
  });

  it('renders heading', () => {
    renderPage();
    expect(screen.getByText(/Chat & Safety Operations/i)).toBeTruthy();
  });

  it('does NOT crash when backend returns {items:[]} (not {sessions:[]})', () => {
    // Primary regression: the old page mapped .sessions, which is undefined
    expect(() => renderPage()).not.toThrow();
  });

  it('renders session rows from items array', async () => {
    renderPage();
    await waitFor(() => {
      const rows = screen.getAllByTestId('table-row');
      expect(rows).toHaveLength(2);
      expect(rows[0].textContent).toBe('sess-1111');
    });
  });

  it('shows loading state while fetching', () => {
    mockedFetchApi.mockReturnValue(new Promise(() => {})); // never resolves
    renderPage();
    expect(screen.getByTestId('loading')).toBeTruthy();
  });

  it('shows error message when API fails', async () => {
    mockedFetchApi.mockRejectedValue(new Error('500 Server Error'));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Failed to load sessions/i)).toBeTruthy();
    });
  });

  it('renders empty state without crashing when items is []', async () => {
    mockedFetchApi.mockResolvedValue({ items: [], total: 0, page: 1, limit: 25 });
    renderPage();
    await waitFor(() => {
      const rows = screen.queryAllByTestId('table-row');
      expect(rows).toHaveLength(0);
    });
  });

  it('renders empty state without crashing when API returns no items key (undefined.map regression)', async () => {
    // Regression guard: { total: 0 } has no items — must not throw undefined.map
    mockedFetchApi.mockResolvedValue({ total: 0, page: 1, limit: 25 });
    expect(() => renderPage()).not.toThrow();
    await waitFor(() => {
      const rows = screen.queryAllByTestId('table-row');
      expect(rows).toHaveLength(0);
    });
  });

  it('handles paginated safety events without crash', () => {
    const safetyPage = {
      items: [
        { id: 'evt-1', chat_session_id: 'sess-1111', user_id: 'user-aaaa', classification: 'PROMPT_INJECTION', action_taken: 'BLOCKED', safe_summary: 'Attempt blocked.', created_at: '2026-09-01T10:05:00Z' },
      ],
      total: 1,
      page: 1,
      limit: 25,
    };
    mockedFetchApi
      .mockResolvedValueOnce(paginatedSessions)
      .mockResolvedValueOnce(safetyPage);
    expect(() => renderPage()).not.toThrow();
  });
});
