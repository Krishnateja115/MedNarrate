import { render, screen } from '@testing-library/react';
import RagOpsPage from '@/app/(protected)/rag-ops/page';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
  useMutation: jest.fn(),
  useQueryClient: jest.fn(),
}));

describe('RagOpsPage', () => {
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

    render(<RagOpsPage />);
    expect(screen.getByText('Knowledge Base & RAG')).toBeInTheDocument();
  });

  it('renders docs correctly', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: {
        status: 'ok',
        documents: [
          {
            id: 'doc-1',
            name: 'Clinical Guidelines',
            version: '1.0',
            status: 'Published',
            approval_state: 'approved',
            updated_at: '2023-10-27T10:00:00Z',
          }
        ],
        overview: {
          index_status: 'healthy',
          total_chunks: 1500,
          total_documents: 1,
          published_documents: 1
        }
      },
      isLoading: false,
      error: null,
    });

    render(<RagOpsPage />);
    expect(screen.getByText('Clinical Guidelines')).toBeInTheDocument();
  });
});
