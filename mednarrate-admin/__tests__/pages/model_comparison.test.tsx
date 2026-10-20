import { render, screen, within } from '@testing-library/react';
import ModelPerformancePage from '@/app/(protected)/model-performance/page';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { buildModelComparison, ModelEntry, ModelPerformanceReport } from '@/lib/model-performance';

jest.mock('@tanstack/react-query', () => ({ useQuery: jest.fn(), useMutation: jest.fn() }));
jest.mock('@/contexts/AuthContext', () => ({ useAuth: jest.fn() }));
jest.mock('@/components/ui/forbidden', () => ({ Forbidden: () => <div>Access denied</div> }));

const entry = (over: Partial<ModelEntry>): ModelEntry => ({
  id: 'x', name: 'x', kind: 'deep_learning', kind_label: 'Deep learning', architecture: '', task: '',
  used_for: '', live: true, dataset: '', primary_metric: '', xai: [], status: 'not_evaluated',
  metrics: [], n: 0, details: {}, ...over,
});
const metric = (key: string, value: number, format: 'percent' | 'points' | 'ms' = 'percent') =>
  ({ key, label: key, format, higher_is_better: true, value });

const large = entry({
  id: 'llm_chain', name: 'Language-model chain', status: 'evaluated',
  metrics: [
    metric('answer_accuracy', 0.9), metric('abstention_rate', 0.8),
    metric('number_preservation', 0.97), metric('sentences_with_all_numbers_kept', 0.9),
    metric('chrf_hindi', 55, 'points'),
  ],
  details: { translation: { avg_latency_ms: 900 } },
});
const small = entry({
  id: 'local_qwen', name: 'Offline model', status: 'evaluated',
  metrics: [
    metric('number_preservation', 0.8), metric('sentences_with_all_numbers_kept', 0.7),
    metric('chrf_hindi', 30, 'points'), metric('avg_latency_ms', 4000, 'ms'),
  ],
});

const report = (models: ModelEntry[]): ModelPerformanceReport => ({
  generated_at: null,
  summary: { total: models.length, evaluated: 0, deep_learning_total: models.length, deep_learning_evaluated: 0 },
  models, xai_methods: [], xai_examples: {},
});

describe('buildModelComparison', () => {
  it('compares only measures both models share and picks the better side', () => {
    const c = buildModelComparison([large, small]);
    expect(c.ready).toBe(true);
    const by = Object.fromEntries(c.shared.map((r) => [r.key, r]));
    expect(by.number_preservation.winner).toBe('large');
    expect(by.chrf_hindi.winner).toBe('large');
    // lower is better for time: 900 ms (large) beats 4000 ms (small)
    expect(by.translation_latency.large).toBe(900);
    expect(by.translation_latency.small).toBe(4000);
    expect(by.translation_latency.winner).toBe('large');
    expect(c.largeOnly.map((r) => r.key)).toEqual(['answer_accuracy', 'abstention_rate']);
  });

  it('lets the small model win when it is faster, and reports ties', () => {
    const fastSmall = entry({ ...small, metrics: [metric('number_preservation', 0.97), metric('avg_latency_ms', 100, 'ms')] });
    const by = Object.fromEntries(buildModelComparison([large, fastSmall]).shared.map((r) => [r.key, r]));
    expect(by.translation_latency.winner).toBe('small');
    expect(by.number_preservation.winner).toBe('tie');
  });

  it('never declares a winner against a model that was not measured', () => {
    const c = buildModelComparison([large, entry({ id: 'local_qwen' })]);
    expect(c.ready).toBe(false);
    expect(c.shared.every((r) => r.small === null && r.winner === null)).toBe(true);
  });

  it('returns no models when the catalog lacks them', () => {
    const c = buildModelComparison([entry({ id: 'other' })]);
    expect(c.large).toBeNull();
    expect(c.small).toBeNull();
  });
});

describe('Large vs small model panel', () => {
  beforeEach(() => {
    (useAuth as jest.Mock).mockReturnValue({ can: () => true });
    (useMutation as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false, isError: false, error: null, data: undefined });
  });

  it('shows both models side by side with measured numbers', () => {
    (useQuery as jest.Mock).mockReturnValue({ data: report([large, small]), isLoading: false, error: null });
    render(<ModelPerformancePage />);
    expect((useQuery as jest.Mock).mock.calls[0][0].refetchInterval).toBe(15_000);
    const panel = screen.getByTestId('model-comparison');
    const row = within(screen.getByTestId('cmp-number_preservation'));
    expect(row.getByText('97.0%')).toBeInTheDocument();
    expect(row.getByText('80.0%')).toBeInTheDocument();
    expect(within(screen.getByTestId('cmp-translation_latency')).getByText('900 ms')).toBeInTheDocument();
    expect(within(screen.getByTestId('cmp-translation_latency')).getByText('4.0 s')).toBeInTheDocument();
    expect(within(panel).getByText(/large model only/i)).toBeInTheDocument();
    expect(within(screen.getByTestId('cmp-answer_accuracy')).getByText('90.0%')).toBeInTheDocument();
  });

  it('says "Not evaluated yet" and how to measure when the small model has no results', () => {
    (useQuery as jest.Mock).mockReturnValue({
      data: report([large, entry({ id: 'local_qwen', name: 'Offline model' })]), isLoading: false, error: null,
    });
    render(<ModelPerformancePage />);
    const panel = screen.getByTestId('model-comparison');
    expect(within(panel).getAllByText('Not evaluated yet').length).toBeGreaterThan(0);
    expect(within(panel).getByText(/no winner is shown/i)).toBeInTheDocument();
    expect(within(panel).getByText(/--only llm,qwen/)).toBeInTheDocument();
  });

  it('is not shown when the catalog has neither model', () => {
    (useQuery as jest.Mock).mockReturnValue({ data: report([entry({ id: 'other' })]), isLoading: false, error: null });
    render(<ModelPerformancePage />);
    expect(screen.queryByTestId('model-comparison')).not.toBeInTheDocument();
  });
});
