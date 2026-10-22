'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { AlertTriangle, BrainCircuit, CheckCircle2, Database, FlaskConical, Layers, Scale, Sparkles } from 'lucide-react';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Forbidden } from '@/components/ui/forbidden';
import { ModelLiveActivity } from '@/components/model-live-activity';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  ClassifierExplanation,
  DatasetInfo,
  EntityExplanation,
  LabTrace,
  ModelEntry,
  ModelPerformanceReport,
  WeightedWord,
  buildModelComparison,
  describeLabRule,
  formatCount,
  formatMetric,
  groupByKind,
} from '@/lib/model-performance';

function WeightBars({ items, unit }: { items: WeightedWord[]; unit: string }) {
  const max = Math.max(...items.map((i) => Math.abs(i.weight)), 1e-9);
  return (
    <ul className="space-y-1.5" aria-label={unit}>
      {items.map((item) => (
        <li key={item.word} className="flex items-center gap-3 text-sm">
          <span className="w-32 shrink-0 truncate font-mono text-xs" title={item.word}>{item.word}</span>
          <div className="relative h-2.5 flex-1 rounded bg-muted">
            <div
              className={`absolute top-0 h-full rounded ${item.weight >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`}
              style={{ width: `${(Math.abs(item.weight) / max) * 100}%` }}
            />
          </div>
          <span className="w-16 shrink-0 text-right font-mono text-xs text-muted-foreground">
            {item.weight >= 0 ? '+' : ''}{item.weight.toFixed(3)}
          </span>
        </li>
      ))}
    </ul>
  );
}

function ClassifierExplanationView({ result }: { result: ClassifierExplanation }) {
  return (
    <div className="space-y-4">
      <p className="text-sm">
        Predicted <strong>{result.predicted}</strong> with {(result.confidence * 100).toFixed(1)}% confidence
        {' '}({Object.entries(result.class_probabilities).map(([k, v]) => `${k} ${(v * 100).toFixed(0)}%`).join(', ')}).
      </p>
      <p className="text-sm text-muted-foreground">
        Why this report type? Green words support the predicted type; red words push against it. Longer bars have
        more influence for this text. Confidence describes the model&apos;s estimate, not medical certainty.
      </p>
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h4 className="mb-1 text-sm font-semibold">LIME (local surrogate)</h4>
          <p className="mb-2 text-xs text-muted-foreground">
            Change in predicted probability when the word is present. Surrogate fit R² = {result.lime.fidelity_r2.toFixed(2)} from {result.lime.samples} perturbed copies.
          </p>
          <WeightBars items={result.lime.features} unit="LIME weights" />
        </div>
        <div>
          <h4 className="mb-1 text-sm font-semibold">Exact linear attribution (SHAP for linear models)</h4>
          <p className="mb-2 text-xs text-muted-foreground">
            Contribution to the model score (log-odds). Intercept {result.linear.intercept.toFixed(2)} plus all {result.linear.feature_count} contributions = {result.linear.score.toFixed(2)}.
          </p>
          <WeightBars items={result.linear.features} unit="Linear contributions" />
        </div>
      </div>
    </div>
  );
}

function EntityExplanationView({ result }: { result: EntityExplanation }) {
  if (result.entities.length === 0) {
    return <p className="text-sm text-muted-foreground">The model found no entities in this text.</p>;
  }
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        The model marked the clinical terms below. Each bar shows how much the other word affected that specific
        term when it was hidden; it does not explain an AI-written summary.
      </p>
      {result.entities.map((ent, idx) => (
        <div key={`${ent.entity}-${idx}`}>
          <p className="text-sm">
            <strong>{ent.entity}</strong>{' '}
            <Badge variant="secondary">{ent.label}</Badge>{' '}
            <span className="text-muted-foreground">confidence {(ent.confidence * 100).toFixed(1)}%</span>
          </p>
          {ent.evidence.length === 0 ? (
            <p className="mt-1 text-xs text-muted-foreground">No other word changed this prediction.</p>
          ) : (
            <div className="mt-2">
              <WeightBars
                items={ent.evidence.map((e) => ({ word: e.word, weight: e.importance }))}
                unit="Occlusion importance"
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function LabTraceView({ trace }: { trace: LabTrace }) {
  return (
    <div className="rounded-lg border p-3 text-sm">
      <div className="mb-1 flex items-center gap-2">
        <strong>{trace.name}</strong>
        <Badge variant="secondary" className="capitalize">{trace.flag.replace('_', ' ')}</Badge>
      </div>
      <p className="text-muted-foreground">{describeLabRule(trace)}</p>
    </div>
  );
}

function StatusBadge({ model }: { model: ModelEntry }) {
  if (model.status === 'evaluated') return <Badge className="bg-emerald-600 hover:bg-emerald-600">Measured</Badge>;
  if (model.status === 'failed') return <Badge variant="destructive">Could not run</Badge>;
  return <Badge variant="outline">Not evaluated yet</Badge>;
}

function DetailsBlock({ model }: { model: ModelEntry }) {
  const d = model.details as Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  const rows: Array<[string, string]> = [];
  if (d.baseline_bm25) {
    const b = d.baseline_bm25 as Record<string, number>;
    rows.push(['Keyword baseline (BM25) Recall@3', formatMetric(b.recall_at_3 ?? 0, 'percent')]);
    rows.push(['Keyword baseline (BM25) MRR', formatMetric(b.mrr ?? 0, 'decimal')]);
  }
  if (d.translation?.number_preservation_by_language) {
    Object.entries(d.translation.number_preservation_by_language as Record<string, number>).forEach(([lang, v]) =>
      rows.push([`Numbers kept (${lang})`, formatMetric(v, 'percent')]),
    );
  }
  if (d.number_preservation_by_language) {
    Object.entries(d.number_preservation_by_language as Record<string, number>).forEach(([lang, v]) =>
      rows.push([`Numbers kept (${lang})`, formatMetric(v, 'percent')]),
    );
  }
  if (d.by_layout) {
    Object.entries(d.by_layout as Record<string, { gold: number; found: number; extra: number; layout: string }>).forEach(
      ([id, v]) => rows.push([`${id.replace(/_/g, ' ')}`, `${v.found}/${v.gold} found, ${v.extra} extra`]),
    );
  }
  const hasMatrix = Array.isArray(d.confusion_matrix) && Array.isArray(d.classes);
  const misses: string[] = d.grounded_qa?.missed_questions ?? [];
  if (rows.length === 0 && !hasMatrix && misses.length === 0 && !d.matching) return null;
  return (
    <details className="mt-3 text-sm">
      <summary className="cursor-pointer font-medium text-muted-foreground">More detail</summary>
      <div className="mt-2 space-y-3">
        {d.matching && <p className="text-xs text-muted-foreground">{String(d.matching)}</p>}
        {rows.length > 0 && (
          <dl className="grid grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2">
            {rows.map(([k, v]) => (
              <div key={k} className="flex justify-between gap-3 border-b py-1">
                <dt className="text-muted-foreground">{k}</dt>
                <dd className="font-mono text-xs">{v}</dd>
              </div>
            ))}
          </dl>
        )}
        {hasMatrix && (
          <table className="text-xs">
            <caption className="mb-1 text-left text-muted-foreground">Confusion matrix (rows = true class)</caption>
            <thead>
              <tr>
                <th className="px-2 py-1" />
                {(d.classes as string[]).map((c) => <th key={c} className="px-2 py-1 font-medium">{c}</th>)}
              </tr>
            </thead>
            <tbody>
              {(d.confusion_matrix as number[][]).map((row, i) => (
                <tr key={i}>
                  <th className="px-2 py-1 text-left font-medium">{(d.classes as string[])[i]}</th>
                  {row.map((v, j) => <td key={j} className="px-2 py-1 text-right font-mono">{v.toLocaleString()}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {misses.length > 0 && (
          <div>
            <p className="text-xs font-medium">Questions answered wrongly</p>
            <ul className="list-disc pl-5 text-xs text-muted-foreground">
              {misses.map((q) => <li key={q}>{q}</li>)}
            </ul>
          </div>
        )}
      </div>
    </details>
  );
}

function ModelCard({ model }: { model: ModelEntry }) {
  return (
    <Card data-testid={`model-${model.id}`}>
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <CardTitle className="text-base">{model.name}</CardTitle>
          <div className="flex flex-wrap gap-1.5">
            <StatusBadge model={model} />
            <Badge variant="secondary">{model.live ? 'Used in the app' : 'Offline / research'}</Badge>
          </div>
        </div>
        <CardDescription>{model.task}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <dl className="grid gap-x-6 gap-y-1 text-xs text-muted-foreground sm:grid-cols-2">
          <div><dt className="inline font-medium">Architecture: </dt><dd className="inline">{model.architecture}</dd></div>
          <div><dt className="inline font-medium">Used for: </dt><dd className="inline">{model.used_for}</dd></div>
          <div className="sm:col-span-2"><dt className="inline font-medium">Measured on: </dt><dd className="inline">{model.dataset}{model.n ? ` (${model.n.toLocaleString()} items)` : ''}</dd></div>
        </dl>

        {model.status === 'evaluated' ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {model.metrics.map((m) => (
              <div key={m.key} className={`rounded-lg border p-3 ${m.key === model.primary_metric ? 'border-primary/50 bg-primary/5' : ''}`}>
                <div className="text-xs text-muted-foreground">{m.label}</div>
                <div className="mt-0.5 text-lg font-semibold">{formatMetric(m.value, m.format)}</div>
              </div>
            ))}
          </div>
        ) : model.status === 'failed' ? (
          <div className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/20 dark:text-amber-300">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>The last evaluation could not run: {model.error}</span>
          </div>
        ) : (
          <p className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
            No scores yet. Run the evaluation script to measure this model.
          </p>
        )}

        {model.note && <p className="text-xs text-muted-foreground">Note: {model.note}</p>}
        {model.evaluated_at && <p className="text-xs text-muted-foreground">Measured: {model.evaluated_at}</p>}
        {model.status === 'evaluated' && <DetailsBlock model={model} />}
      </CardContent>
    </Card>
  );
}

type ExplainKind = 'report-type' | 'entities';
type ExplainResult = ClassifierExplanation | EntityExplanation;

function TryItPanel() {
  const [text, setText] = useState('');
  const [kind, setKind] = useState<ExplainKind | null>(null);
  const mutation = useMutation<ExplainResult, Error, { kind: ExplainKind; text: string }>({
    mutationFn: ({ kind: k, text: t }) => fetchApi(`/api/v1/admin/ml/explain/${k}`, { data: { text: t } }),
  });
  const run = (k: ExplainKind) => {
    setKind(k);
    mutation.mutate({ kind: k, text });
  };
  const result = mutation.data;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><Sparkles className="h-5 w-5" /> Explain your own text</CardTitle>
        <CardDescription>
          Paste a short extract without patient names. Run an explanation to see which words influenced the
          report-type prediction or clinical-term labels. Only the text length is written to the audit log.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. Histopathology: invasive ductal carcinoma, tumor size 2.1 cm, lymph nodes negative"
          maxLength={3000}
          aria-label="Text to explain"
          rows={4}
        />
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => run('report-type')} disabled={!text.trim() || mutation.isPending}>
            Explain report-type classifier
          </Button>
          <Button variant="outline" onClick={() => run('entities')} disabled={!text.trim() || mutation.isPending}>
            Explain entity recognition (max 60 words)
          </Button>
        </div>
        {mutation.isPending && <Skeleton className="h-24 w-full" />}
        {mutation.isError && (
          <p role="alert" className="text-sm text-destructive">{mutation.error?.message || 'The explanation failed.'}</p>
        )}
        {result && !mutation.isPending && (
          <div className="rounded-lg border p-4">
            {kind === 'report-type' && 'predicted' in result ? (
              <ClassifierExplanationView result={result} />
            ) : 'entities' in result ? (
              <EntityExplanationView result={result} />
            ) : null}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function ModelPerformancePage() {
  const { can } = useAuth();
  const allowed = can('ai.view') || can('ai.manage');
  const { data, isLoading, error } = useQuery<ModelPerformanceReport>({
    queryKey: ['model_performance'],
    queryFn: () => fetchApi('/api/v1/admin/ml/model-performance'),
    enabled: allowed,
    refetchInterval: 15_000,
    refetchOnWindowFocus: true,
  });

  if (!allowed) return <Forbidden />;

  const examples = data?.xai_examples ?? {};
  const pending = data ? data.summary.deep_learning_total - data.summary.deep_learning_evaluated : 0;

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Models &amp; Explainability</h1>
        <p className="text-muted-foreground">
          See why a specific report type or clinical term was identified. Evaluation scores are in Performance.
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-4">{[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 w-full" />)}</div>
      ) : error || !data ? (
        <div className="p-8 text-center text-destructive">Failed to load model performance.</div>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <SummaryCard title="Models measured" value={`${data.summary.evaluated} / ${data.summary.total}`} icon={<CheckCircle2 className="h-4 w-4 text-emerald-500" />} />
            <SummaryCard title="Deep-learning models measured" value={`${data.summary.deep_learning_evaluated} / ${data.summary.deep_learning_total}`} icon={<BrainCircuit className="h-4 w-4 text-blue-500" />} />
            <SummaryCard title="Explainability methods" value={String(data.xai_methods.length)} icon={<Layers className="h-4 w-4 text-purple-500" />} />
            <SummaryCard title="Last evaluation run" value={data.generated_at ? new Date(data.generated_at).toLocaleString() : 'Never'} icon={<FlaskConical className="h-4 w-4 text-muted-foreground" />} small />
          </div>

          <Tabs defaultValue="xai" className="space-y-4">
            <TabsList>
              <TabsTrigger value="xai">Explainability (XAI)</TabsTrigger>
              <TabsTrigger value="performance">Performance</TabsTrigger>
            </TabsList>

            <TabsContent value="performance" className="space-y-8">
              <ModelLiveActivity />
              {pending > 0 && (
                <Card className="border-amber-300 bg-amber-50 dark:bg-amber-950/20">
                  <CardContent className="flex items-start gap-3 pt-4">
                    <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
                    <p className="text-sm text-amber-800 dark:text-amber-300">
                      {pending} deep-learning {pending === 1 ? 'model has' : 'models have'} not been measured yet.{' '}
                      {data.how_to_refresh}
                    </p>
                  </CardContent>
                </Card>
              )}
              <ModelComparisonCard models={data.models} />
              {groupByKind(data.models).map((group) => (
                <section key={group.kind} className="space-y-3">
                  <h2 className="text-lg font-semibold">{group.label}</h2>
                  {group.models.map((m) => <ModelCard key={m.id} model={m} />)}
                </section>
              ))}
              {data.dataset && data.dataset.records_usable ? <DatasetCard info={data.dataset} /> : null}
              <p className="text-xs text-muted-foreground">
                Scores come from small, hand-checked test sets in the repository, so they show relative strengths and
                weaknesses rather than clinical accuracy. Latency depends on the machine that ran the evaluation.
              </p>
            </TabsContent>

            <TabsContent value="xai" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">What these explanations show</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm text-muted-foreground">
                  <p>For report classification, see which words pushed the predicted report type up or down.</p>
                  <p>For clinical terms, see which surrounding words influenced each label. Lab flags show the
                    measured value and reference range used by the rule.</p>
                  <p>These explanations are for those specific models and rules. They do not explain how the
                    hosted language model wrote a medical summary or prove that a result is clinically correct.</p>
                </CardContent>
              </Card>

              <TryItPanel />

              <div className="grid gap-4 md:grid-cols-2">
                {data.xai_methods.map((m) => (
                  <Card key={m.id}>
                    <CardHeader className="pb-2"><CardTitle className="text-base">{m.name}</CardTitle></CardHeader>
                    <CardContent className="text-sm text-muted-foreground">{m.summary}</CardContent>
                  </Card>
                ))}
              </div>

              {examples.classifier?.map((ex) => (
                <Card key={ex.title}>
                  <CardHeader>
                    <CardTitle className="text-base">Report-type classifier: {ex.title}</CardTitle>
                    <CardDescription className="font-mono text-xs">{ex.text}</CardDescription>
                  </CardHeader>
                  <CardContent><ClassifierExplanationView result={ex} /></CardContent>
                </Card>
              ))}

              {examples.ner?.map((ex, i) => (
                <Card key={`${ex.text}-${i}`}>
                  <CardHeader>
                    <CardTitle className="text-base">Entity recognition: what the model leaned on</CardTitle>
                    <CardDescription className="font-mono text-xs">{ex.text}</CardDescription>
                  </CardHeader>
                  <CardContent><EntityExplanationView result={ex} /></CardContent>
                </Card>
              ))}

              {examples.lab && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Why a lab value is flagged High or Low</CardTitle>
                    <CardDescription>The rule trace shown to patients in the app.</CardDescription>
                  </CardHeader>
                  <CardContent className="grid gap-3 md:grid-cols-3">
                    {examples.lab.map((t) => <LabTraceView key={t.name} trace={t} />)}
                  </CardContent>
                </Card>
              )}

              {!examples.classifier && !examples.ner && (
                <p className="text-sm text-muted-foreground">
                  Worked examples appear after the evaluation script has run. You can use the box above now.
                </p>
              )}
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}

function DatasetCard({ info }: { info: DatasetInfo }) {
  const rows: [string, string][] = [
    ['Usable reports', formatCount(info.records_usable)],
    ['Unique patients', formatCount(info.unique_patients)],
    ['Duplicates removed', formatCount(info.duplicates_removed)],
    [
      'Train / validation / test',
      `${formatCount(info.train_records)} / ${formatCount(info.validation_records)} / ${formatCount(info.test_records)}`,
    ],
    ['Classes', (info.classes ?? []).join(', ') || '—'],
  ];
  return (
    <Card data-testid="dataset-card">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Database className="h-4 w-4 text-blue-500" /> Training dataset: {info.name}
        </CardTitle>
        {info.task ? <CardDescription>{info.task}</CardDescription> : null}
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <dl className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
          {rows.map(([k, v]) => (
            <div key={k} className="flex justify-between gap-3 border-b py-1">
              <dt className="text-muted-foreground">{k}</dt>
              <dd className="font-medium">{v}</dd>
            </div>
          ))}
        </dl>
        {info.split ? <p className="text-muted-foreground">{info.split}</p> : null}
        {info.leakage_safeguard ? <p className="text-muted-foreground">{info.leakage_safeguard}</p> : null}
        {info.scope ? <p className="text-xs text-muted-foreground">{info.scope}</p> : null}
      </CardContent>
    </Card>
  );
}

function SummaryCard({ title, value, icon, small }: { title: string; value: string; icon: React.ReactNode; small?: boolean }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className={small ? 'text-base font-semibold' : 'text-2xl font-bold'}>{value}</div>
      </CardContent>
    </Card>
  );
}

function ModelComparisonCard({ models }: { models: ModelEntry[] }) {
  const cmp = buildModelComparison(models);
  if (!cmp.large || !cmp.small) return null;

  const show = (v: number | null, row: { format: Parameters<typeof formatMetric>[1] }) =>
    v === null ? 'Not evaluated yet' : formatMetric(v, row.format);
  const cell = (row: { winner: string | null }, side: 'large' | 'small') =>
    row.winner === side ? 'font-semibold text-emerald-700 dark:text-emerald-400' : '';

  return (
    <Card data-testid="model-comparison">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Scale className="h-4 w-4 text-blue-500" /> Large model vs small model
        </CardTitle>
        <CardDescription>
          The hosted language-model chain (large) next to the offline Qwen2.5-1.5B model (small), on the same
          translation test sentences.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {!cmp.ready && (
          <p className="rounded border border-amber-300 bg-amber-50 p-3 text-amber-800 dark:bg-amber-950/20 dark:text-amber-300">
            At least one of the two models has not been measured yet, so no winner is shown.
            Run <code>python scripts/evaluate_models.py --only llm,qwen</code> in mednarrate-backend and reload.
          </p>
        )}
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="py-1.5 pr-3 font-medium">Measure</th>
                <th className="py-1.5 pr-3 font-medium">Large (hosted chain)</th>
                <th className="py-1.5 font-medium">Small (offline Qwen)</th>
              </tr>
            </thead>
            <tbody>
              {cmp.shared.map((row) => (
                <tr key={row.key} className="border-b last:border-0" data-testid={`cmp-${row.key}`}>
                  <td className="py-1.5 pr-3">
                    {row.label}
                    <span className="ml-1 text-xs text-muted-foreground">
                      ({row.higherIsBetter ? 'higher is better' : 'lower is better'})
                    </span>
                  </td>
                  <td className={`py-1.5 pr-3 ${cell(row, 'large')}`}>{show(row.large, row)}</td>
                  <td className={`py-1.5 ${cell(row, 'small')}`}>{show(row.small, row)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {cmp.largeOnly.some((r) => r.large !== null) && (
          <div>
            <h4 className="mb-1 font-semibold">Measured for the large model only</h4>
            <ul className="space-y-0.5 text-muted-foreground">
              {cmp.largeOnly.filter((r) => r.large !== null).map((r) => (
                <li key={r.key} data-testid={`cmp-${r.key}`}>
                  {r.label}: <span className="font-medium text-foreground">{formatMetric(r.large as number, r.format)}</span>
                </li>
              ))}
            </ul>
            <p className="mt-1 text-xs text-muted-foreground">
              The small model is only used for translation, so it has no score for these.
            </p>
          </div>
        )}
        <p className="text-xs text-muted-foreground">
          Green marks the better value. Times depend on the machine that ran the evaluation: the large model runs on
          the provider&apos;s servers, the small one on the evaluation machine&apos;s CPU. Both use small, hand-checked
          test sets, so a gap shows a trend, not clinical accuracy.
        </p>
      </CardContent>
    </Card>
  );
}
