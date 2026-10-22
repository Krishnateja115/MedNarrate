import { fireEvent, render, screen } from '@testing-library/react';
import ModelPerformancePage from '@/app/(protected)/model-performance/page';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import {
  describeLabRule,
  formatMetric,
  groupByKind,
  ModelEntry,
  ModelPerformanceReport,
} from '@/lib/model-performance';

jest.mock('@tanstack/react-query', () => ({
  useQuery: jest.fn(),
  useMutation: jest.fn(),
}));

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

jest.mock('@/components/ui/forbidden', () => ({
  Forbidden: () => <div>Access denied</div>,
}));

const baseModel: ModelEntry = {
  id: 'biomedical_ner',
  name: 'Biomedical NER',
  kind: 'deep_learning',
  kind_label: 'Deep learning',
  architecture: 'Transformer',
  task: 'Finds clinical terms',
  used_for: 'Highlights terms',
  live: true,
  dataset: 'Hand-labelled sentences',
  primary_metric: 'f1',
  xai: ['occlusion'],
  status: 'not_evaluated',
  metrics: [],
  n: 0,
  details: {},
};

const report = (models: ModelEntry[], extra: Partial<ModelPerformanceReport> = {}): ModelPerformanceReport => ({
  generated_at: null,
  summary: {
    total: models.length,
    evaluated: models.filter((m) => m.status === 'evaluated').length,
    deep_learning_total: models.filter((m) => m.kind === 'deep_learning').length,
    deep_learning_evaluated: models.filter((m) => m.kind === 'deep_learning' && m.status === 'evaluated').length,
  },
  models,
  xai_methods: [
    { id: 'lime', name: 'LIME (local surrogate)', summary: 'Hides words and refits.' },
    { id: 'occlusion', name: 'Occlusion saliency', summary: 'Blanks one word at a time.' },
  ],
  xai_examples: {},
  how_to_refresh: 'Run `python scripts/evaluate_models.py` in mednarrate-backend and reload.',
  ...extra,
});

const mockQuery = (data: ModelPerformanceReport | null, isLoading = false, error: Error | null = null) =>
  (useQuery as jest.Mock).mockReturnValue({ data, isLoading, error });

const showPerformance = () => {
  const tab = screen.getByRole('tab', { name: 'Performance' });
  fireEvent.mouseDown(tab);
  fireEvent.click(tab);
};

describe('ModelPerformancePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({ can: () => true });
    (useMutation as jest.Mock).mockReturnValue({
      mutate: jest.fn(), isPending: false, isError: false, error: null, data: undefined,
    });
  });

  it('shows the heading while loading', () => {
    mockQuery(null, true);
    render(<ModelPerformancePage />);
    expect(screen.getByText('Models & Explainability')).toBeInTheDocument();
  });

  it('is forbidden without the ai.view permission', () => {
    (useAuth as jest.Mock).mockReturnValue({ can: () => false });
    mockQuery(null);
    render(<ModelPerformancePage />);
    expect(screen.getByText('Access denied')).toBeInTheDocument();
    expect(screen.queryByText('Models & Explainability')).not.toBeInTheDocument();
  });

  it('says "Not evaluated yet" instead of showing numbers, and explains how to measure', () => {
    mockQuery(report([baseModel]));
    render(<ModelPerformancePage />);
    showPerformance();
    expect(screen.getByText('Not evaluated yet')).toBeInTheDocument();
    expect(screen.getByText(/No scores yet/)).toBeInTheDocument();
    expect(screen.getByText(/1 deep-learning model has not been measured yet/)).toBeInTheDocument();
    expect(screen.getByText(/scripts\/evaluate_models\.py/)).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it('shows measured scores with their formatting', () => {
    const measured: ModelEntry = {
      ...baseModel,
      status: 'evaluated',
      n: 25,
      metrics: [
        { key: 'f1', label: 'F1 score', format: 'percent', higher_is_better: true, value: 0.853 },
        { key: 'avg_latency_ms', label: 'Average latency', format: 'ms', higher_is_better: false, value: 42.4 },
      ],
    };
    mockQuery(report([measured], { generated_at: '2026-10-18T10:00:00+00:00' }));
    render(<ModelPerformancePage />);
    showPerformance();
    expect(screen.getByText('Measured')).toBeInTheDocument();
    expect(screen.getByText('85.3%')).toBeInTheDocument();
    expect(screen.getByText('42 ms')).toBeInTheDocument();
    expect(screen.getByText(/25 items/)).toBeInTheDocument();
    expect(screen.queryByText(/have not been measured yet/)).not.toBeInTheDocument();
  });

  it('shows the training dataset card with counts when the server sends it', () => {
    mockQuery(report([baseModel], {
      dataset: {
        name: 'MRAD (Unified Medical Dataset)',
        task: 'Report type: Blood / Health / TCGA',
        classes: ['Blood', 'Health', 'TCGA'],
        records_usable: 123367,
        unique_patients: 110677,
        duplicates_removed: 12,
        train_records: 98000,
        validation_records: 12000,
        test_records: 13367,
        split: 'Split by patient so no patient is in two sets.',
      },
    }));
    render(<ModelPerformancePage />);
    showPerformance();
    expect(screen.getByTestId('dataset-card')).toBeInTheDocument();
    expect(screen.getByText(/MRAD \(Unified Medical Dataset\)/)).toBeInTheDocument();
    expect(screen.getByText('123,367')).toBeInTheDocument();
    expect(screen.getByText('110,677')).toBeInTheDocument();
    expect(screen.getByText('98,000 / 12,000 / 13,367')).toBeInTheDocument();
  });

  it('shows no dataset card when the dataset info is missing or empty', () => {
    mockQuery(report([baseModel]));
    const { unmount } = render(<ModelPerformancePage />);
    expect(screen.queryByTestId('dataset-card')).not.toBeInTheDocument();
    unmount();
    mockQuery(report([baseModel], { dataset: { name: 'MRAD', records_usable: null } }));
    render(<ModelPerformancePage />);
    expect(screen.queryByTestId('dataset-card')).not.toBeInTheDocument();
  });

  it('reports a failed evaluation with its reason', () => {
    mockQuery(report([{ ...baseModel, status: 'failed', error: 'No Gemini key configured' }]));
    render(<ModelPerformancePage />);
    showPerformance();
    expect(screen.getByText('Could not run')).toBeInTheDocument();
    expect(screen.getByText(/No Gemini key configured/)).toBeInTheDocument();
  });

  it('groups models by kind', () => {
    const rules: ModelEntry = { ...baseModel, id: 'lab', name: 'Lab extractor', kind: 'rule_based', kind_label: 'Rule-based' };
    mockQuery(report([baseModel, rules]));
    render(<ModelPerformancePage />);
    showPerformance();
    expect(screen.getByText('Deep learning')).toBeInTheDocument();
    expect(screen.getByText('Rule-based')).toBeInTheDocument();
  });

  it('opens on explanations, with the text explanation before performance metrics', () => {
    mockQuery(report([baseModel]));
    render(<ModelPerformancePage />);
    expect(screen.getByRole('tab', { name: /Explainability/ })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText('What these explanations show')).toBeInTheDocument();
    expect(screen.getByText(/They do not explain how the hosted language model/)).toBeInTheDocument();
    expect(screen.getByText('LIME (local surrogate)')).toBeInTheDocument();
    expect(screen.getByText('Occlusion saliency')).toBeInTheDocument();
    expect(screen.getByLabelText('Text to explain')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Explain report-type classifier/ })).toBeDisabled();
  });

  it('sends the pasted text to the explain endpoint', () => {
    const mutate = jest.fn();
    (useMutation as jest.Mock).mockReturnValue({ mutate, isPending: false, isError: false, error: null, data: undefined });
    mockQuery(report([baseModel]));
    render(<ModelPerformancePage />);
    fireEvent.change(screen.getByLabelText('Text to explain'), { target: { value: 'tumor size 2 cm' } });
    fireEvent.click(screen.getByRole('button', { name: /Explain report-type classifier/ }));
    expect(mutate).toHaveBeenCalledWith({ kind: 'report-type', text: 'tumor size 2 cm' });
  });
});

describe('model-performance helpers', () => {
  it('formats each metric type', () => {
    expect(formatMetric(0.9, 'percent')).toBe('90.0%');
    expect(formatMetric(0.8123, 'decimal')).toBe('0.812');
    expect(formatMetric(250, 'ms')).toBe('250 ms');
    expect(formatMetric(2500, 'ms')).toBe('2.5 s');
    expect(formatMetric(61.234, 'points')).toBe('61.2 / 100');
  });

  it('describes lab rule traces in plain language', () => {
    const base = { name: 'Hb', value: 11.2, unit: 'g/dL', ref_low: 13, ref_high: 17, flag: 'low', distance: 1.8, distance_percent: 13.8 };
    expect(describeLabRule({ ...base, rule: 'value_below_low' })).toBe(
      '11.2 g/dL is below the lowest normal value (13 g/dL) by 13.8%, so it is flagged Low.',
    );
    expect(describeLabRule({ ...base, value: 18, rule: 'value_above_high' })).toContain('flagged High');
    expect(describeLabRule({ ...base, rule: 'value_within_range' })).toContain('Normal');
    expect(describeLabRule({ ...base, rule: 'no_reference_range' })).toContain('cannot be flagged');
  });

  it('keeps the kind order and drops empty groups', () => {
    const groups = groupByKind([
      { ...baseModel, kind: 'rule_based', kind_label: 'Rule-based' },
      baseModel,
    ]);
    expect(groups.map((g) => g.kind)).toEqual(['deep_learning', 'rule_based']);
  });
});
