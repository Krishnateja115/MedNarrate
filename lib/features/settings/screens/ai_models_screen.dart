import 'package:flutter/material.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/api_service.dart';
import '../../../core/utils/lab_flag_trace.dart';
import '../../reports/widgets/lab_flag_sheet.dart';
import '../models/model_performance.dart';

/// "AI models & explainability": how each model scored on our own tests, and
/// worked examples of the explainability (XAI) methods. Every number comes from
/// the server's last evaluation run; a model that was never measured says so
/// instead of showing a made-up score.
class AiModelsScreen extends StatefulWidget {
  const AiModelsScreen({super.key});

  @override
  State<AiModelsScreen> createState() => _AiModelsScreenState();
}

class _AiModelsScreenState extends State<AiModelsScreen> {
  late Future<ModelPerformanceReport> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiService.instance.getModelPerformance();
  }

  Future<void> _reload() async {
    final next = ApiService.instance.getModelPerformance();
    setState(() => _future = next);
    try {
      await next;
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Text(l.mlScreenTitle, style: const TextStyle(fontWeight: FontWeight.bold)),
        elevation: 0,
      ),
      body: FutureBuilder<ModelPerformanceReport>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError || snap.data == null) {
            final message = snap.error is ApiException
                ? (snap.error as ApiException).message
                : l.mlLoadError;
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(message, textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    OutlinedButton(onPressed: _reload, child: Text(l.retry)),
                  ],
                ),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: _reload,
            child: _Body(report: snap.data!),
          );
        },
      ),
    );
  }
}

// ───────────────────────── label helpers ─────────────────────────

String mlKindLabel(AppLocalizations l, String kind, String fallback) {
  switch (kind) {
    case 'deep_learning':
      return l.mlKindDeep;
    case 'classical_ml':
      return l.mlKindClassical;
    case 'rule_based':
      return l.mlKindRules;
    default:
      return fallback;
  }
}

String mlTaskText(AppLocalizations l, String id, String fallback) {
  switch (id) {
    case 'biomedical_ner':
      return l.mlTaskBiomedicalNer;
    case 'report_embedding':
      return l.mlTaskReportEmbedding;
    case 'kb_embedding':
      return l.mlTaskKbEmbedding;
    case 'pubmedbert_embedding':
      return l.mlTaskPubmedbertEmbedding;
    case 'llm_chain':
      return l.mlTaskLlmChain;
    case 'local_qwen':
      return l.mlTaskLocalQwen;
    case 'whisper_stt':
      return l.mlTaskWhisperStt;
    case 'report_classifier':
      return l.mlTaskReportClassifier;
    case 'lab_extractor':
      return l.mlTaskLabExtractor;
    default:
      return fallback;
  }
}

String mlMetricLabel(AppLocalizations l, ModelMetric m) {
  switch (m.key) {
    case 'precision':
      return l.mlMetricPrecision;
    case 'recall':
      return l.mlMetricRecall;
    case 'f1':
      return l.mlMetricF1;
    case 'label_accuracy':
      return l.mlMetricEntityType;
    case 'avg_latency_ms':
      return l.mlMetricAvgLatency;
    case 'latency_p50_ms':
      return l.mlMetricLatencyP50;
    case 'latency_p95_ms':
      return l.mlMetricLatencyP95;
    case 'recall_at_1':
      return l.mlMetricTop1;
    case 'recall_at_3':
      return l.mlMetricTop3;
    case 'recall_at_5':
      return l.mlMetricTop5;
    case 'mrr':
      return l.mlMetricMrr;
    case 'answer_accuracy':
      return l.mlMetricAnswerAccuracy;
    case 'abstention_rate':
      return l.mlMetricAbstention;
    case 'number_preservation':
      return l.mlMetricNumbersKept;
    case 'sentences_with_all_numbers_kept':
      return l.mlMetricAllNumbers;
    case 'chrf_hindi':
      return l.mlMetricChrf;
    case 'wer_en':
      return l.mlMetricWerEn;
    case 'wer_hi':
      return l.mlMetricWerHi;
    case 'accuracy':
      return l.mlMetricAccuracy;
    case 'macro_precision':
      return l.mlMetricMacroPrecision;
    case 'macro_recall':
      return l.mlMetricMacroRecall;
    case 'macro_f1':
      return l.mlMetricMacroF1;
    default:
      return m.label;
  }
}

// ───────────────────────────── body ─────────────────────────────

class _Body extends StatelessWidget {
  final ModelPerformanceReport report;
  const _Body({required this.report});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final muted = theme.colorScheme.onSurface.withValues(alpha: 0.65);
    const kinds = ['deep_learning', 'classical_ml', 'rule_based'];
    final pending = report.deepTotal - report.deepEvaluated;

    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
      children: [
        Text(l.mlIntro, style: TextStyle(fontSize: 14, height: 1.45, color: muted)),
        const SizedBox(height: 14),
        Row(
          children: [
            Expanded(
              child: _SummaryTile(
                  icon: Icons.fact_check_outlined,
                  text: l.mlSummaryMeasured(report.evaluated, report.total)),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _SummaryTile(
                  icon: Icons.psychology_outlined,
                  text: l.mlSummaryDeep(report.deepEvaluated, report.deepTotal)),
            ),
          ],
        ),
        if (report.generatedAt != null) ...[
          const SizedBox(height: 8),
          Text(l.mlLastMeasured(_formatWhen(report.generatedAt!)),
              style: TextStyle(fontSize: 12, color: muted)),
        ],
        if (pending > 0) ...[
          const SizedBox(height: 12),
          _Banner(text: l.mlPendingBanner),
        ],
        for (final kind in kinds)
          if (report.models.any((m) => m.kind == kind)) ...[
            const SizedBox(height: 22),
            Text(
              mlKindLabel(l, kind,
                  report.models.firstWhere((m) => m.kind == kind).kindLabel),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            for (final model in report.models.where((m) => m.kind == kind))
              _ModelCard(model: model),
          ],
        const SizedBox(height: 6),
        Text(l.mlTestSetNote, style: TextStyle(fontSize: 12, height: 1.4, color: muted)),
        const SizedBox(height: 26),
        _XaiSection(report: report),
      ],
    );
  }

  static String _formatWhen(String iso) {
    final parsed = DateTime.tryParse(iso);
    if (parsed == null) return iso;
    final d = parsed.toLocal();
    String two(int v) => v.toString().padLeft(2, '0');
    return '${d.year}-${two(d.month)}-${two(d.day)} ${two(d.hour)}:${two(d.minute)}';
  }
}

class _SummaryTile extends StatelessWidget {
  final IconData icon;
  final String text;
  const _SummaryTile({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.primary, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Text(text,
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, height: 1.3)),
          ),
        ],
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  final String text;
  const _Banner({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.amber.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.amber.withValues(alpha: 0.5)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline, size: 18, color: Colors.amber),
          const SizedBox(width: 10),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 13, height: 1.4))),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String text;
  final Color color;
  const _Chip(this.text, this.color);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.13),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(text,
          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: color)),
    );
  }
}

class _ModelCard extends StatelessWidget {
  final ModelEntry model;
  const _ModelCard({required this.model});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final muted = theme.colorScheme.onSurface.withValues(alpha: 0.65);
    final statusLabel = model.isEvaluated
        ? l.mlStatusMeasured
        : model.status == 'failed'
            ? l.mlStatusFailed
            : l.mlStatusNotEvaluated;
    final statusColor = model.isEvaluated
        ? const Color(0xFF00A67E)
        : model.status == 'failed'
            ? Colors.redAccent
            : Colors.grey;

    return Container(
      key: ValueKey('model-${model.id}'),
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(model.name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              _Chip(statusLabel, statusColor),
              _Chip(model.live ? l.mlUsedInApp : l.mlOfflineTool, AppColors.primary),
            ],
          ),
          const SizedBox(height: 8),
          Text(mlTaskText(l, model.id, model.task),
              style: TextStyle(fontSize: 13, height: 1.4, color: muted)),
          const SizedBox(height: 12),
          if (model.isEvaluated) ...[
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final metric in model.metrics)
                  _MetricTile(
                    label: mlMetricLabel(l, metric),
                    value: metric.formatted,
                    highlight: metric.key == model.primaryMetric,
                  ),
              ],
            ),
            if (model.n > 0) ...[
              const SizedBox(height: 10),
              Text(l.mlMeasuredOn(model.n), style: TextStyle(fontSize: 12, color: muted)),
            ],
          ] else
            Text(l.mlNoScoresYet,
                style: TextStyle(fontSize: 13, fontStyle: FontStyle.italic, color: muted)),
        ],
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  final String label;
  final String value;
  final bool highlight;
  const _MetricTile({required this.label, required this.value, required this.highlight});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      constraints: const BoxConstraints(minWidth: 96, maxWidth: 160),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: highlight
            ? AppColors.primary.withValues(alpha: 0.08)
            : theme.colorScheme.onSurface.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
            color: highlight
                ? AppColors.primary.withValues(alpha: 0.45)
                : theme.colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(value, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
          const SizedBox(height: 2),
          Text(label,
              style: TextStyle(
                  fontSize: 11,
                  height: 1.25,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.65))),
        ],
      ),
    );
  }
}

// ───────────────────────────── XAI ─────────────────────────────

class _XaiSection extends StatelessWidget {
  final ModelPerformanceReport report;
  const _XaiSection({required this.report});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final muted = theme.colorScheme.onSurface.withValues(alpha: 0.65);
    final methods = <(String, String)>[
      (l.mlXaiLimeName, l.mlXaiLimeBody),
      (l.mlXaiLinearName, l.mlXaiLinearBody),
      (l.mlXaiOcclusionName, l.mlXaiOcclusionBody),
      (l.mlXaiRuleName, l.mlXaiRuleBody),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(l.mlXaiTitle, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        const SizedBox(height: 6),
        Text(l.mlXaiIntro, style: TextStyle(fontSize: 14, height: 1.45, color: muted)),
        const SizedBox(height: 12),
        for (final (name, body) in methods)
          Container(
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.cardColor,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: theme.colorScheme.outlineVariant),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(body, style: TextStyle(fontSize: 13, height: 1.4, color: muted)),
              ],
            ),
          ),
        for (final ex in report.classifierExamples) _ClassifierExampleCard(example: ex),
        for (final ex in report.entityExamples) _EntityExampleCard(example: ex),
        if (report.labExamples.isNotEmpty) _LabExamplesCard(examples: report.labExamples),
        if (report.classifierExamples.isNotEmpty ||
            report.entityExamples.isNotEmpty ||
            report.labExamples.isNotEmpty)
          Text(l.mlXaiExampleNote, style: TextStyle(fontSize: 12, color: muted)),
      ],
    );
  }
}

class _ExampleFrame extends StatelessWidget {
  final String title;
  final String text;
  final List<Widget> children;
  const _ExampleFrame({required this.title, required this.text, required this.children});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.bold)),
          if (text.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(text,
                style: TextStyle(
                    fontSize: 12,
                    fontFamily: 'monospace',
                    height: 1.35,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7))),
          ],
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }
}

class _ClassifierExampleCard extends StatelessWidget {
  final ClassifierExample example;
  const _ClassifierExampleCard({required this.example});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context)!;
    return _ExampleFrame(
      title: l.mlXaiClassifierTitle,
      text: example.text,
      children: [
        Text(
          l.mlXaiPredicted(example.predicted, (example.confidence * 100).toStringAsFixed(0)),
          style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 12),
        _Caption(l.mlXaiLimeCaption),
        WordBars(words: example.lime),
        const SizedBox(height: 12),
        _Caption(l.mlXaiLinearCaption),
        WordBars(words: example.linear),
      ],
    );
  }
}

class _EntityExampleCard extends StatelessWidget {
  final EntityExample example;
  const _EntityExampleCard({required this.example});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context)!;
    return _ExampleFrame(
      title: l.mlXaiEntitiesTitle,
      text: example.text,
      children: [
        for (final e in example.entities) ...[
          Text('${e.entity}  ·  ${e.label}  ·  ${(e.confidence * 100).toStringAsFixed(0)}%',
              style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          if (e.evidence.isEmpty)
            Text(l.mlXaiNoEvidence,
                style: TextStyle(
                    fontSize: 12.5,
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6)))
          else ...[
            _Caption(l.mlXaiEvidenceCaption),
            WordBars(words: e.evidence),
          ],
          const SizedBox(height: 12),
        ],
      ],
    );
  }
}

class _LabExamplesCard extends StatelessWidget {
  final List<LabExample> examples;
  const _LabExamplesCard({required this.examples});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context)!;
    return _ExampleFrame(
      title: l.mlXaiLabsTitle,
      text: '',
      children: [
        for (final ex in examples) ...[
          Builder(builder: (context) {
            final trace = LabFlagTrace.compute(
              value: ex.value,
              unit: ex.unit,
              refLow: ex.refLow,
              refHigh: ex.refHigh,
              flag: ex.flag,
            );
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(ex.name, style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(labFlagSentence(l, trace), style: const TextStyle(fontSize: 13, height: 1.4)),
                const SizedBox(height: 10),
              ],
            );
          }),
        ],
      ],
    );
  }
}

class _Caption extends StatelessWidget {
  final String text;
  const _Caption(this.text);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(text,
            style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.65))),
      );
}

/// Horizontal bars: green pushes towards the prediction, red pushes away.
class WordBars extends StatelessWidget {
  final List<WeightedWord> words;
  const WordBars({super.key, required this.words});

  @override
  Widget build(BuildContext context) {
    if (words.isEmpty) return const SizedBox.shrink();
    final theme = Theme.of(context);
    final maxAbs = words
        .map((w) => w.weight.abs())
        .fold<double>(1e-9, (a, b) => b > a ? b : a);
    return Column(
      children: [
        for (final w in words)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(
              children: [
                SizedBox(
                  width: 96,
                  child: Text(w.word,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 12, fontFamily: 'monospace')),
                ),
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: (w.weight.abs() / maxAbs).clamp(0.02, 1.0).toDouble(),
                      minHeight: 8,
                      backgroundColor: theme.colorScheme.onSurface.withValues(alpha: 0.08),
                      valueColor: AlwaysStoppedAnimation<Color>(
                          w.weight >= 0 ? const Color(0xFF00A67E) : Colors.redAccent),
                    ),
                  ),
                ),
                SizedBox(
                  width: 56,
                  child: Text('${w.weight >= 0 ? '+' : ''}${w.weight.toStringAsFixed(3)}',
                      textAlign: TextAlign.end,
                      style: TextStyle(
                          fontSize: 11,
                          fontFamily: 'monospace',
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.6))),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
