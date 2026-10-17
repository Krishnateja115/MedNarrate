/// Read-only view of the server's model-performance report
/// (`GET /ml/model-performance`). Nothing here is computed on the device.
library;

double? _num(Object? v) => v is num ? v.toDouble() : null;

class ModelMetric {
  final String key;
  final String label;
  final String format; // percent | decimal | ms | points
  final bool higherIsBetter;
  final double value;

  const ModelMetric({
    required this.key,
    required this.label,
    required this.format,
    required this.higherIsBetter,
    required this.value,
  });

  factory ModelMetric.fromMap(Map<String, dynamic> m) => ModelMetric(
        key: m['key'] as String? ?? '',
        label: m['label'] as String? ?? '',
        format: m['format'] as String? ?? 'decimal',
        higherIsBetter: m['higher_is_better'] as bool? ?? true,
        value: _num(m['value']) ?? 0,
      );

  /// "85.3%", "42 ms", "2.5 s", "61.2 / 100" or "0.812".
  String get formatted {
    switch (format) {
      case 'percent':
        return '${(value * 100).toStringAsFixed(1)}%';
      case 'ms':
        return value >= 1000
            ? '${(value / 1000).toStringAsFixed(1)} s'
            : '${value.round()} ms';
      case 'points':
        return '${value.toStringAsFixed(1)} / 100';
      default:
        return value.toStringAsFixed(3);
    }
  }
}

class ModelEntry {
  final String id;
  final String name;
  final String kind; // deep_learning | classical_ml | rule_based
  final String kindLabel;
  final String task;
  final bool live;
  final String primaryMetric;
  final String status; // evaluated | not_evaluated | failed
  final List<ModelMetric> metrics;
  final int n;
  final String? evaluatedAt;
  final String? note;

  const ModelEntry({
    required this.id,
    required this.name,
    required this.kind,
    required this.kindLabel,
    required this.task,
    required this.live,
    required this.primaryMetric,
    required this.status,
    required this.metrics,
    required this.n,
    this.evaluatedAt,
    this.note,
  });

  bool get isEvaluated => status == 'evaluated';
  bool get isDeepLearning => kind == 'deep_learning';

  factory ModelEntry.fromMap(Map<String, dynamic> m) => ModelEntry(
        id: m['id'] as String? ?? '',
        name: m['name'] as String? ?? '',
        kind: m['kind'] as String? ?? '',
        kindLabel: m['kind_label'] as String? ?? '',
        task: m['task'] as String? ?? '',
        live: m['live'] as bool? ?? false,
        primaryMetric: m['primary_metric'] as String? ?? '',
        status: m['status'] as String? ?? 'not_evaluated',
        metrics: [
          for (final x in (m['metrics'] as List? ?? const []))
            ModelMetric.fromMap(Map<String, dynamic>.from(x as Map)),
        ],
        n: (m['n'] as num?)?.toInt() ?? 0,
        evaluatedAt: m['evaluated_at'] as String?,
        note: m['note'] as String?,
      );
}

class WeightedWord {
  final String word;
  final double weight;
  const WeightedWord(this.word, this.weight);

  static List<WeightedWord> listFrom(Object? raw, {String weightKey = 'weight'}) => [
        for (final x in (raw as List? ?? const []))
          WeightedWord((x as Map)['word'] as String? ?? '', _num(x[weightKey]) ?? 0),
      ];
}

class ClassifierExample {
  final String text;
  final String predicted;
  final double confidence;
  final List<WeightedWord> lime;
  final List<WeightedWord> linear;

  const ClassifierExample({
    required this.text,
    required this.predicted,
    required this.confidence,
    required this.lime,
    required this.linear,
  });

  factory ClassifierExample.fromMap(Map<String, dynamic> m) => ClassifierExample(
        text: m['text'] as String? ?? '',
        predicted: m['predicted'] as String? ?? '',
        confidence: _num(m['confidence']) ?? 0,
        lime: WeightedWord.listFrom((m['lime'] as Map?)?['features']),
        linear: WeightedWord.listFrom((m['linear'] as Map?)?['features']),
      );
}

class EntityEvidence {
  final String entity;
  final String label;
  final double confidence;
  final List<WeightedWord> evidence;
  const EntityEvidence(this.entity, this.label, this.confidence, this.evidence);
}

class EntityExample {
  final String text;
  final List<EntityEvidence> entities;
  const EntityExample(this.text, this.entities);

  factory EntityExample.fromMap(Map<String, dynamic> m) => EntityExample(
        m['text'] as String? ?? '',
        [
          for (final e in (m['entities'] as List? ?? const []))
            EntityEvidence(
              (e as Map)['entity'] as String? ?? '',
              e['label'] as String? ?? '',
              _num(e['confidence']) ?? 0,
              WeightedWord.listFrom(e['evidence'], weightKey: 'importance'),
            ),
        ],
      );
}

/// One lab value used as a worked example of the rule trace.
class LabExample {
  final String name;
  final double value;
  final String unit;
  final double? refLow;
  final double? refHigh;
  final String flag;
  const LabExample(this.name, this.value, this.unit, this.refLow, this.refHigh, this.flag);

  factory LabExample.fromMap(Map<String, dynamic> m) => LabExample(
        m['name'] as String? ?? '',
        _num(m['value']) ?? 0,
        m['unit'] as String? ?? '',
        _num(m['ref_low']),
        _num(m['ref_high']),
        m['flag'] as String? ?? 'not_classified',
      );
}

class ModelPerformanceReport {
  final String? generatedAt;
  final int total;
  final int evaluated;
  final int deepTotal;
  final int deepEvaluated;
  final List<ModelEntry> models;
  final List<ClassifierExample> classifierExamples;
  final List<EntityExample> entityExamples;
  final List<LabExample> labExamples;

  const ModelPerformanceReport({
    required this.generatedAt,
    required this.total,
    required this.evaluated,
    required this.deepTotal,
    required this.deepEvaluated,
    required this.models,
    required this.classifierExamples,
    required this.entityExamples,
    required this.labExamples,
  });

  factory ModelPerformanceReport.fromMap(Map<String, dynamic> m) {
    final summary = Map<String, dynamic>.from(m['summary'] as Map? ?? const {});
    final examples = Map<String, dynamic>.from(m['xai_examples'] as Map? ?? const {});
    List<T> mapList<T>(Object? raw, T Function(Map<String, dynamic>) f) => [
          for (final x in (raw as List? ?? const []))
            f(Map<String, dynamic>.from(x as Map)),
        ];
    return ModelPerformanceReport(
      generatedAt: m['generated_at'] as String?,
      total: (summary['total'] as num?)?.toInt() ?? 0,
      evaluated: (summary['evaluated'] as num?)?.toInt() ?? 0,
      deepTotal: (summary['deep_learning_total'] as num?)?.toInt() ?? 0,
      deepEvaluated: (summary['deep_learning_evaluated'] as num?)?.toInt() ?? 0,
      models: mapList(m['models'], ModelEntry.fromMap),
      classifierExamples: mapList(examples['classifier'], ClassifierExample.fromMap),
      entityExamples: mapList(examples['ner'], EntityExample.fromMap),
      labExamples: mapList(examples['lab'], LabExample.fromMap),
    );
  }
}
