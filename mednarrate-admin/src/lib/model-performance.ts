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
