import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/l10n/locale_notifier.dart';
import 'package:mednarrate/core/utils/lab_flag_trace.dart';
import 'package:mednarrate/features/reports/widgets/lab_flag_sheet.dart';
import 'package:mednarrate/features/settings/models/model_performance.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

void main() {
  group('LabFlagTrace', () {
    test('value below the range is Low and says by how much', () {
      final t = LabFlagTrace.compute(
          value: 11.2, unit: 'g/dL', refLow: 13, refHigh: 17, flag: 'low');
      expect(t.rule, LabFlagRule.belowLow);
      expect(t.computedFlag, 'low');
      expect(t.distance, closeTo(1.8, 1e-9));
      expect(t.distancePercent, closeTo(13.846, 0.01));
      expect(t.agreesWithFlag, isTrue);
    });

    test('value above the range is High', () {
      final t = LabFlagTrace.compute(
          value: 11500, refLow: 4000, refHigh: 10000, flag: 'high');
      expect(t.rule, LabFlagRule.aboveHigh);
      expect(t.distancePercent, closeTo(15.0, 1e-9));
    });

    test('inside the range is Normal and has no distance', () {
      final t = LabFlagTrace.compute(
          value: 180000, refLow: 150000, refHigh: 410000, flag: 'normal');
      expect(t.rule, LabFlagRule.withinRange);
      expect(t.distance, isNull);
    });

    test('one-sided and missing ranges', () {
      final upperOnly = LabFlagTrace.compute(value: 250, refHigh: 200);
      expect(upperOnly.rule, LabFlagRule.aboveHigh);
      final none = LabFlagTrace.compute(value: 3);
      expect(none.rule, LabFlagRule.noRange);
      expect(none.markerPosition, isNull);
    });

    test("the laboratory's own marking wins and is reported as a disagreement", () {
      final t = LabFlagTrace.compute(
          value: 14, refLow: 13, refHigh: 17, flag: 'high');
      expect(t.computedFlag, 'normal');
      expect(t.agreesWithFlag, isFalse);
      expect(LabFlagTrace.compute(value: 14, refLow: 13, refHigh: 17, flag: 'critical').agreesWithFlag, isFalse);
    });

    test('marker sits left of, inside and right of the shaded range', () {
      double pos(double v) =>
          LabFlagTrace.compute(value: v, refLow: 10, refHigh: 20).markerPosition!;
      expect(pos(0), lessThan(0.25));
      expect(pos(15), closeTo(0.5, 1e-9));
      expect(pos(40), greaterThan(0.75));
      expect(pos(-1000), 0.04);
      expect(pos(1000), 0.96);
    });

    test('numbers print without noise', () {
      expect(LabFlagTrace.formatNumber(13), '13');
      expect(LabFlagTrace.formatNumber(11.2), '11.2');
      expect(LabFlagTrace.formatNumber(0.350), '0.35');
      expect(LabFlagTrace.formatNumber(2.456), '2.46');
    });
  });

  group('ModelPerformanceReport', () {
    final json = <String, dynamic>{
      'generated_at': '2026-10-18T10:00:00+00:00',
      'summary': {
        'total': 2,
        'evaluated': 1,
        'deep_learning_total': 1,
        'deep_learning_evaluated': 0,
      },
      'models': [
        {
          'id': 'biomedical_ner',
          'name': 'Biomedical NER',
          'kind': 'deep_learning',
          'kind_label': 'Deep learning',
          'task': 'Finds terms',
          'live': true,
          'primary_metric': 'f1',
          'status': 'not_evaluated',
          'metrics': [],
          'n': 0,
        },
        {
          'id': 'lab_extractor',
          'name': 'Lab extractor',
          'kind': 'rule_based',
          'kind_label': 'Rule-based',
          'task': 'Reads labs',
          'live': true,
          'primary_metric': 'f1',
          'status': 'evaluated',
          'metrics': [
            {'key': 'f1', 'label': 'F1 score', 'format': 'percent', 'higher_is_better': true, 'value': 0.8947},
            {'key': 'avg_latency_ms', 'label': 'Average latency', 'format': 'ms', 'higher_is_better': false, 'value': 2500},
            {'key': 'chrf_hindi', 'label': 'chrF', 'format': 'points', 'higher_is_better': true, 'value': 61.234},
            {'key': 'mrr', 'label': 'MRR', 'format': 'decimal', 'higher_is_better': true, 'value': 0.8123},
          ],
          'n': 42,
        },
      ],
      'xai_examples': {
        'classifier': [
          {
            'text': 'tumor size 2 cm',
            'predicted': 'TCGA',
            'confidence': 0.97,
            'lime': {'features': [{'word': 'tumor', 'weight': 0.065}]},
            'linear': {'features': [{'word': 'tumor', 'weight': 0.38}]},
          }
        ],
        'ner': [
          {
            'text': 'takes metformin for diabetes',
            'entities': [
              {
                'entity': 'diabetes',
                'label': 'Disease_disorder',
                'confidence': 0.9,
                'evidence': [{'word': 'metformin', 'importance': 0.3}],
              }
            ],
          }
        ],
        'lab': [
          {'name': 'Hemoglobin', 'value': 11.2, 'unit': 'g/dL', 'ref_low': 13, 'ref_high': 17, 'flag': 'low'}
        ],
      },
    };

    test('parses models, statuses and examples', () {
      final r = ModelPerformanceReport.fromMap(json);
      expect(r.total, 2);
      expect(r.deepEvaluated, 0);
      expect(r.models.first.isEvaluated, isFalse);
      expect(r.models.first.metrics, isEmpty);
      expect(r.models.last.isEvaluated, isTrue);
      expect(r.classifierExamples.single.lime.single.word, 'tumor');
      expect(r.entityExamples.single.entities.single.evidence.single.weight, 0.3);
      expect(r.labExamples.single.refLow, 13);
    });

    test('formats each metric type', () {
      final metrics = ModelPerformanceReport.fromMap(json).models.last.metrics;
      expect(metrics.map((m) => m.formatted).toList(),
          ['89.5%', '2.5 s', '61.2 / 100', '0.812']);
    });

    test('an empty or partial reply does not crash', () {
      final r = ModelPerformanceReport.fromMap(<String, dynamic>{});
      expect(r.models, isEmpty);
      expect(r.classifierExamples, isEmpty);
      expect(r.generatedAt, isNull);
    });
  });

  group('Why flagged? sheet', () {
    setUp(() => localeModeNotifier.value = const Locale('en'));

    Widget host(Widget child, {Locale locale = const Locale('en')}) => MaterialApp(
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          locale: locale,
          home: Scaffold(body: child),
        );

    testWidgets('explains a Low result with the numbers behind it', (tester) async {
      await tester.pumpWidget(host(LabFlagSheet(
        testName: 'Hemoglobin',
        trace: LabFlagTrace.compute(
            value: 11.2, unit: 'g/dL', refLow: 13, refHigh: 17, flag: 'low'),
        isProvisional: false,
      )));
      expect(find.text('How this result was flagged'), findsOneWidget);
      expect(find.text('Hemoglobin'), findsOneWidget);
      expect(find.text('11.2 g/dL'), findsOneWidget);
      expect(find.text('13 – 17 g/dL'), findsOneWidget);
      expect(
        find.text('11.2 g/dL is below the lowest normal value (13 g/dL) by 13.8%, so it is flagged “Low”.'),
        findsOneWidget,
      );
      expect(find.textContaining('does not diagnose'), findsOneWidget);
    });

    testWidgets("says when the laboratory's marking was used", (tester) async {
      await tester.pumpWidget(host(LabFlagSheet(
        testName: 'Glucose',
        trace: LabFlagTrace.compute(value: 90, refLow: 70, refHigh: 99, flag: 'high'),
        isProvisional: false,
      )));
      expect(find.textContaining('marked this result as “High”'), findsOneWidget);
    });

    testWidgets('notes a general (provisional) range', (tester) async {
      await tester.pumpWidget(host(LabFlagSheet(
        testName: 'Monocytes',
        trace: LabFlagTrace.compute(value: 9, unit: '%', refLow: 2, refHigh: 8, flag: 'high'),
        isProvisional: true,
      )));
      expect(find.textContaining('general adult range'), findsOneWidget);
    });

    testWidgets('has no range bar and says so when no range exists', (tester) async {
      await tester.pumpWidget(host(LabFlagSheet(
        testName: 'Vitamin X',
        trace: LabFlagTrace.compute(value: 3),
        isProvisional: false,
      )));
      expect(find.textContaining('cannot be flagged'), findsOneWidget);
    });

    testWidgets('speaks Hindi when the app is in Hindi', (tester) async {
      localeModeNotifier.value = const Locale('hi');
      await tester.pumpWidget(host(
        LabFlagSheet(
          testName: 'हीमोग्लोबिन',
          trace: LabFlagTrace.compute(value: 11.2, unit: 'g/dL', refLow: 13, refHigh: 17, flag: 'low'),
          isProvisional: false,
        ),
        locale: const Locale('hi'),
      ));
      expect(find.text('इस नतीजे पर निशान कैसे लगा'), findsOneWidget);
      expect(find.text('आपका मान'), findsOneWidget);
    });
  });
}
