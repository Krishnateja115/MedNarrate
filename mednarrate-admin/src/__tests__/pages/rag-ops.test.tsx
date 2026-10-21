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
jest.mock('@/components/ui/select', () => ({
  Select: ({ value, onValueChange, disabled, children }: { value: string; onValueChange: (value: string) => void; disabled?: boolean; children: React.ReactNode }) => (
    <select value={value} disabled={disabled} onChange={(event) => onValueChange(event.target.value)}>{children}</select>
  ),
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectContent: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectValue: () => null,
  SelectItem: ({ value, children }: { value: string; children: React.ReactNode }) => <option value={value}>{children}</option>,
}));
jest.mock('@/components/ui/data-table', () => ({
  DataTable: ({ data, isLoading, columns }: {
    data: Array<{ id: string }>;
    isLoading?: boolean;
    columns: Array<{ id?: string; cell?: (context: { row: { original: { id: string } } }) => React.ReactNode }>;
  }) => (
    <div data-testid="data-table">
      {isLoading ? (
        <div data-testid="loading">loading</div>
      ) : (
        <ul>
          {data.map((row, i) => (
            <li key={i} data-testid="doc-row">
              {row.id}
              {columns.find((column) => column.id === 'actions')?.cell?.({ row: { original: row } })}
            </li>
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
      expect(rows[0].textContent).toContain('doc-aaa');
    });
  });

  it('sends a JSON payload when archiving a document', async () => {
    renderPage();
    showDocuments();
    await waitFor(() => expect(screen.getAllByTestId('doc-row')).toHaveLength(2));
    fireEvent.change(screen.getAllByRole('combobox')[1], { target: { value: 'Archived' } });
    await waitFor(() => expect(mockedFetchApi).toHaveBeenCalledWith(
      '/api/v1/admin/rag-ops/documents/doc-aaa/status',
      { method: 'PATCH', data: { status: 'Archived' } },
    ));
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

  it('shows the chat search details when the backend sends them', async () => {
    mockedFetchApi.mockImplementation((url) => {
      if ((url as string).includes('/status')) {
        return Promise.resolve({
          status: 'ok',
          overview: {
            ...ragStatus.overview,
            report_search: {
              embeddings_enabled: true,
              embedding_provider: 'gemini',
              vector_size: 768,
              search_mode: 'embeddings_with_keyword_backup',
              reports_indexed: 3,
              report_chunks: 9,
              chunks_with_vectors: 7,
              chunks_without_vectors: 2,
            },
            health_notes: { passages: 21, ready: true },
          },
        });
      }
      return Promise.resolve(paginatedDocs);
    });
    renderPage();
    await waitFor(() => expect(screen.getByText('Embeddings + keyword backup')).toBeTruthy());
    expect(screen.getByText(/Provider: gemini/)).toBeTruthy();
    expect(screen.getByText('7 / 9')).toBeTruthy();
    expect(screen.getByText('21 passages')).toBeTruthy();
    expect(screen.getByText(/2 report chunk\(s\) have no vector yet/)).toBeTruthy();
  });

  it('warns when embeddings are off and the health notes are not built', async () => {
    mockedFetchApi.mockImplementation((url) => {
      if ((url as string).includes('/status')) {
        return Promise.resolve({
          status: 'ok',
          overview: {
            ...ragStatus.overview,
            report_search: {
              embeddings_enabled: false,
              embedding_provider: null,
              vector_size: 768,
              search_mode: 'keyword_only',
              reports_indexed: 0,
              report_chunks: 0,
              chunks_with_vectors: 0,
              chunks_without_vectors: 0,
            },
            health_notes: { passages: 0, ready: false },
          },
        });
      }
      return Promise.resolve(paginatedDocs);
    });
    renderPage();
    await waitFor(() => expect(screen.getByText('Keyword only')).toBeTruthy());
    expect(screen.getByText('Not built')).toBeTruthy();
  });

  it('still renders when an older backend sends no chat search details', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('142')).toBeTruthy());
    expect(screen.queryByText('Chat search')).toBeNull();
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
