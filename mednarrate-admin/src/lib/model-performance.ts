export type ModelKind = 'deep_learning' | 'classical_ml' | 'rule_based';
export type ModelStatus = 'evaluated' | 'not_evaluated' | 'failed';
export type MetricFormat = 'percent' | 'decimal' | 'ms' | 'points';

export interface ModelMetric {
  key: string;
  label: string;
  format: MetricFormat;
  higher_is_better: boolean;
  value: number;
}

export interface ModelEntry {
  id: string;
  name: string;
  kind: ModelKind;
  kind_label: string;
  architecture: string;
  task: string;
  used_for: string;
  live: boolean;
  dataset: string;
  primary_metric: string;
  xai: string[];
  status: ModelStatus;
  metrics: ModelMetric[];
  n: number;
  details: Record<string, unknown>;
  evaluated_at?: string | null;
  note?: string;
  error?: string;
}

export interface XaiMethod {
  id: string;
  name: string;
  summary: string;
}

export interface WeightedWord {
  word: string;
  weight: number;
}

export interface ClassifierExplanation {
  predicted: string;
  confidence: number;
  class_probabilities: Record<string, number>;
  lime: { features: WeightedWord[]; fidelity_r2: number; samples: number };
  linear: { features: WeightedWord[]; intercept: number; score: number; feature_count: number };
}

export interface EntityExplanation {
  method: 'occlusion';
  entities: Array<{
    entity: string;
    label: string;
    confidence: number;
    evidence: Array<{ word: string; importance: number }>;
  }>;
}

export interface LabTrace {
  name: string;
  value: number;
  unit: string;
  ref_low: number | null;
  ref_high: number | null;
  flag: string;
  rule: string;
  distance: number | null;
  distance_percent: number | null;
}

export interface XaiExamples {
  classifier?: Array<ClassifierExplanation & { title: string; text: string }>;
  ner?: Array<EntityExplanation & { title: string; text: string }>;
  lab?: LabTrace[];
}

export interface DatasetInfo {
  name: string;
  task?: string;
  classes?: string[];
  records_raw?: number | null;
  records_usable?: number | null;
  duplicates_removed?: number | null;
  unique_patients?: number | null;
  train_records?: number | null;
  validation_records?: number | null;
  test_records?: number | null;
  test_support_by_class?: Record<string, number>;
  split?: string;
  random_seed?: number | null;
  leakage_safeguard?: string;
  scope?: string;
}

export function formatCount(value: number | null | undefined): string {
  return typeof value === 'number' ? value.toLocaleString('en-US') : '—';
}

export interface ModelPerformanceReport {
  generated_at: string | null;
  environment?: Record<string, string>;
  summary: {
    total: number;
    evaluated: number;
    deep_learning_total: number;
    deep_learning_evaluated: number;
  };
  models: ModelEntry[];
  xai_methods: XaiMethod[];
  xai_examples: XaiExamples;
  dataset?: DatasetInfo | null;
  how_to_refresh?: string;
}

export function formatMetric(value: number, format: MetricFormat): string {
  switch (format) {
    case 'percent':
      return `${(value * 100).toFixed(1)}%`;
    case 'ms':
      return value >= 1000 ? `${(value / 1000).toFixed(1)} s` : `${Math.round(value)} ms`;
    case 'points':
      return `${value.toFixed(1)} / 100`;
    default:
      return value.toFixed(3);
  }
}

/** Plain-language sentence for a rule-trace, e.g. "11.2 g/dL is below the lowest normal value (13)". */
export function describeLabRule(trace: LabTrace): string {
  const unit = trace.unit ? ` ${trace.unit}` : '';
  const value = `${trace.value}${unit}`;
  switch (trace.rule) {
    case 'value_below_low':
      return `${value} is below the lowest normal value (${trace.ref_low}${unit})${
        trace.distance_percent != null ? ` by ${trace.distance_percent.toFixed(1)}%` : ''
      }, so it is flagged Low.`;
    case 'value_above_high':
      return `${value} is above the highest normal value (${trace.ref_high}${unit})${
        trace.distance_percent != null ? ` by ${trace.distance_percent.toFixed(1)}%` : ''
      }, so it is flagged High.`;
    case 'value_within_range':
      return `${value} is inside the reference range (${trace.ref_low ?? '…'} to ${trace.ref_high ?? '…'}${unit}), so it is Normal.`;
    case 'no_reference_range':
      return `${value} has no reference range in the report, so it cannot be flagged.`;
    default:
      return 'This value is not numeric, so no flag was computed.';
  }
}

export const KIND_ORDER: ModelKind[] = ['deep_learning', 'classical_ml', 'rule_based'];

export function groupByKind(models: ModelEntry[]): Array<{ kind: ModelKind; label: string; models: ModelEntry[] }> {
  return KIND_ORDER.map((kind) => ({
    kind,
    label: models.find((m) => m.kind === kind)?.kind_label ?? kind,
    models: models.filter((m) => m.kind === kind),
  })).filter((g) => g.models.length > 0);
}

export const LARGE_MODEL_ID = 'llm_chain';
export const SMALL_MODEL_ID = 'local_qwen';

export type ComparisonWinner = 'large' | 'small' | 'tie' | null;

export interface ComparisonRow {
  key: string;
  label: string;
  format: MetricFormat;
  higherIsBetter: boolean;
  large: number | null;
  small: number | null;
  /** Which model is ahead; null when either side has no measurement. */
  winner: ComparisonWinner;
  /** True when only the large model is tested on this measure. */
  largeOnly?: boolean;
}

export interface ModelComparison {
  large: ModelEntry | null;
  small: ModelEntry | null;
  /** True only when both models have measured results. */
  ready: boolean;
  shared: ComparisonRow[];
  largeOnly: ComparisonRow[];
}

function metricValue(model: ModelEntry | null, key: string): number | null {
  if (!model || model.status !== 'evaluated') return null;
  const m = model.metrics.find((x) => x.key === key);
  return m ? m.value : null;
}

function pickWinner(large: number | null, small: number | null, higherIsBetter: boolean): ComparisonWinner {
  if (large === null || small === null) return null;
  if (Math.abs(large - small) < 1e-9) return 'tie';
  const largeAhead = higherIsBetter ? large > small : large < small;
  return largeAhead ? 'large' : 'small';
}

/** Average time per translated sentence for the hosted chain, recorded under details.translation. */
function largeTranslationLatency(model: ModelEntry | null): number | null {
  if (!model || model.status !== 'evaluated') return null;
  const translation = (model.details as { translation?: { avg_latency_ms?: unknown } }).translation;
  const v = translation?.avg_latency_ms;
  return typeof v === 'number' ? v : null;
}

/**
 * Side-by-side view of the hosted language-model chain (large) and the offline Qwen model (small).
 * Only measures taken the same way for both models are compared: the translation test sentences and
 * the average time per translated sentence. Answer accuracy and abstention are only measured for the
 * large model and are listed separately, never as a comparison.
 */
export function buildModelComparison(models: ModelEntry[]): ModelComparison {
  const large = models.find((m) => m.id === LARGE_MODEL_ID) ?? null;
  const small = models.find((m) => m.id === SMALL_MODEL_ID) ?? null;

  const sharedSpecs: Array<Pick<ComparisonRow, 'key' | 'label' | 'format' | 'higherIsBetter'>> = [
    { key: 'number_preservation', label: 'Numbers kept in translation', format: 'percent', higherIsBetter: true },
    { key: 'sentences_with_all_numbers_kept', label: 'Sentences with every number kept', format: 'percent', higherIsBetter: true },
    { key: 'chrf_hindi', label: 'Hindi translation quality (chrF)', format: 'points', higherIsBetter: true },
  ];
  const shared: ComparisonRow[] = sharedSpecs.map((r) => {
    const l = metricValue(large, r.key);
    const s = metricValue(small, r.key);
    return { ...r, large: l, small: s, winner: pickWinner(l, s, r.higherIsBetter) };
  });

  const l = largeTranslationLatency(large);
  const s = metricValue(small, 'avg_latency_ms');
  shared.push({
    key: 'translation_latency',
    label: 'Average time per translated sentence',
    format: 'ms',
    higherIsBetter: false,
    large: l,
    small: s,
    winner: pickWinner(l, s, false),
  });

  const largeOnlySpecs: Array<Pick<ComparisonRow, 'key' | 'label' | 'format'>> = [
    { key: 'answer_accuracy', label: 'Answers questions from a report correctly', format: 'percent' },
    { key: 'abstention_rate', label: 'Says "not in the report" when it is not', format: 'percent' },
  ];
  const largeOnly: ComparisonRow[] = largeOnlySpecs.map((r) => ({
    ...r,
    higherIsBetter: true,
    large: metricValue(large, r.key),
    small: null,
    winner: null,
    largeOnly: true,
  }));

  return {
    large,
    small,
    ready: !!large && !!small && large.status === 'evaluated' && small.status === 'evaluated',
    shared,
    largeOnly,
  };
}
