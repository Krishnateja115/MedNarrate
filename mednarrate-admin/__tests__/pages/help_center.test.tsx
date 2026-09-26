import { fireEvent, render, screen } from '@testing-library/react';
import { useMutation, useQuery } from '@tanstack/react-query';
import HelpCenterPage from '@/app/(protected)/help-center/page';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
  useMutation: jest.fn(),
  useQueryClient: () => ({ invalidateQueries: jest.fn() }),
}));

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ can: (permission: string) => permission === 'help_center.manage' }),
}));

const article = {
  id: 'art-1',
  title: 'Why is my report still processing?',
  slug: 'why-is-my-report-still-processing',
  category: 'Reports',
  summary: 'What to check when report processing has not completed.',
  content: 'Keep the report ID and contact support if processing does not complete.',
  status: 'published',
  author: 'MedNarrate',
  created_at: '2026-09-26T10:00:00Z',
  updated_at: '2026-09-26T10:00:00Z',
  published_at: '2026-09-26T10:00:00Z',
};

describe('HelpCenterPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useMutation as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
  });

  it('renders the loading state', () => {
    (useQuery as jest.Mock).mockReturnValue({ data: null, isLoading: true, error: null });
    render(<HelpCenterPage />);
    expect(screen.getByTestId('help-center-loading')).toBeInTheDocument();
  });

  it('renders useful article metadata and filters', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: { status: 'ok', categories: ['Reports', 'Privacy'], articles: [article] },
      isLoading: false,
      error: null,
    });
    render(<HelpCenterPage />);

    expect(screen.getByText(article.title)).toBeInTheDocument();
    expect(screen.getByText(article.summary)).toBeInTheDocument();
    expect(screen.getAllByText('Published')).toHaveLength(2);
    expect(screen.getByLabelText('Search articles')).toBeInTheDocument();
    expect(screen.getByLabelText('Filter by category')).toBeInTheDocument();
    expect(screen.getByLabelText('Filter by status')).toBeInTheDocument();
  });

  it('supports article preview', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: { status: 'ok', categories: ['Reports'], articles: [article] },
      isLoading: false,
      error: null,
    });
    render(<HelpCenterPage />);
    fireEvent.click(screen.getByRole('button', { name: /preview/i }));
    expect(screen.getByText(article.content)).toBeInTheDocument();
  });

  it('opens the create editor for managers', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: { status: 'ok', categories: ['Account', 'Reports'], articles: [] },
      isLoading: false,
      error: null,
    });
    render(<HelpCenterPage />);
    fireEvent.click(screen.getByRole('button', { name: /new article/i }));
    expect(screen.getByText('Create article')).toBeInTheDocument();
    expect(screen.getByLabelText('Title')).toBeInTheDocument();
    expect(screen.getByLabelText('Content')).toBeInTheDocument();
  });
});
