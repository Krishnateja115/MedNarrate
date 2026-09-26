/**
 * Regression tests for rag-ops/page.tsx
 *
 * Specifically guards against:
 * - undefined.map() crash when backend returns {items:[]} instead of {documents:[]}
 * - Safe rendering under: empty, loading, API error, failed ingestion, degraded health
 */
import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import RagOpsPage from '@/app/(protected)/rag-ops/page';

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
jest.mock('@/components/ui/toast', () => ({
  toast: { add: jest.fn() },
}));
jest.mock('@/components/ui/data-table', () => ({
  DataTable: ({ data, isLoading }: { data: unknown[]; isLoading?: boolean }) => (
    <div data-testid="data-table">
      {isLoading ? (
        <div data-testid="loading">loading</div>
      ) : (
        <ul>
          {(data as Array<{ id: string }>).map((row, i) => (
            <li key={i} data-testid="doc-row">{row.id}</li>
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
      <RagOpsPage />
    </QueryClientProvider>
  );

const showDocuments = () => fireEvent.click(screen.getByRole('tab', { name: 'Documents' }));

// ─── fixtures ─────────────────────────────────────────────────────────────────
const ragStatus = {
  status: 'ok',
  overview: {
    index_status: 'healthy',
    error_summary: null,
    total_chunks: 142,
    total_documents: 2,
    published_documents: 1,
    failed_documents: 0,
  },
};

const ragStatusDegraded = {
  status: 'ok',
  overview: {
    index_status: 'down',
    error_summary: 'Vector store not reachable',
    total_chunks: 0,
    total_documents: 2,
    published_documents: 0,
    failed_documents: 2,
  },
};

const paginatedDocs = {
  items: [
    { id: 'doc-aaa', name: 'Cardiology Guidelines', version: '1.0', status: 'Published', approval_state: 'approved', created_at: '2026-09-01T10:00:00Z', updated_at: '2026-09-10T10:00:00Z' },
    { id: 'doc-bbb', name: 'Diabetes Protocol', version: '2.1', status: 'Draft', approval_state: null, created_at: '2026-09-05T10:00:00Z', updated_at: '2026-09-06T10:00:00Z' },
  ],
  total: 2,
  page: 1,
  limit: 25,
};

// ─── tests ────────────────────────────────────────────────────────────────────
describe('RagOpsPage', () => {
  beforeEach(() => {
    mockedFetchApi.mockReset();
    // Default: status succeeds, docs succeed
    mockedFetchApi.mockImplementation((url) => {
      if ((url as string).includes('/status')) return Promise.resolve(ragStatus);
      return Promise.resolve(paginatedDocs);
    });
  });

  it('renders heading', () => {
    renderPage();
    expect(screen.getByText(/Knowledge Base & RAG/i)).toBeTruthy();
  });

  it('does NOT crash when backend returns {items:[]} (not {documents:[]})', () => {
    // Primary regression: the old page mapped .documents, which is undefined
    expect(() => renderPage()).not.toThrow();
  });

  it('renders document rows from items array', async () => {
    renderPage();
    showDocuments();
    await waitFor(() => {
      const rows = screen.getAllByTestId('doc-row');
      expect(rows).toHaveLength(2);
      expect(rows[0].textContent).toBe('doc-aaa');
    });
  });

  it('shows loading state while fetching', () => {
    mockedFetchApi.mockReturnValue(new Promise(() => {})); // never resolves
    const { container } = renderPage();
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('shows error message when documents API fails', async () => {
    mockedFetchApi.mockRejectedValue(new Error('503 Service Unavailable'));
    renderPage();
    showDocuments();
    await waitFor(() => {
      expect(screen.getByText(/Failed to load documents/i)).toBeTruthy();
    });
  });

  it('renders empty state without crashing when items is []', async () => {
    mockedFetchApi.mockImplementation((url) => {
      if ((url as string).includes('/status')) return Promise.resolve(ragStatus);
      return Promise.resolve({ items: [], total: 0, page: 1, limit: 25 });
    });
    renderPage();
    showDocuments();
    await waitFor(() => {
      const rows = screen.queryAllByTestId('doc-row');
      expect(rows).toHaveLength(0);
    });
  });

  it('renders empty state without crashing when items key is missing (undefined.map regression)', async () => {
    mockedFetchApi.mockImplementation((url) => {
      if ((url as string).includes('/status')) return Promise.resolve(ragStatus);
      return Promise.resolve({ total: 0, page: 1, limit: 25 }); // no items key
    });
    expect(() => renderPage()).not.toThrow();
    showDocuments();
    await waitFor(() => {
      const rows = screen.queryAllByTestId('doc-row');
      expect(rows).toHaveLength(0);
    });
  });

  it('renders failed documents alert when failed_documents > 0', async () => {
    mockedFetchApi.mockImplementation((url) => {
      if ((url as string).includes('/status')) return Promise.resolve(ragStatusDegraded);
      return Promise.resolve(paginatedDocs);
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/failed ingestion/i)).toBeTruthy();
    });
  });

  it('renders error summary when vector store is down', async () => {
    mockedFetchApi.mockImplementation((url) => {
      if ((url as string).includes('/status')) return Promise.resolve(ragStatusDegraded);
      return Promise.resolve(paginatedDocs);
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Vector store not reachable/i)).toBeTruthy();
    });
  });
});
