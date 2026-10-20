import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/features/reports/models/document_type_check.dart';
import 'package:mednarrate/features/reports/widgets/document_type_badge.dart';
import 'package:mednarrate/features/settings/models/model_performance.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

Widget _host(Widget child) => MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('en'),
      home: Scaffold(body: child),
    );

void main() {
  group('DocumentTypeCheck', () {
    test('parses a confident answer', () {
      final c = DocumentTypeCheck.fromMap(
          {'enabled': true, 'available': true, 'label': 'Blood', 'confidence': 0.874});
      expect(c.isShown, isTrue);
      expect(c.percent, 87);
    });

    test('feature off, unavailable, odd label or no score is never shown', () {
      expect(DocumentTypeCheck.fromMap({'enabled': false, 'available': false}).isShown, isFalse);
      expect(DocumentTypeCheck.fromMap({'enabled': true, 'available': false}).isShown, isFalse);
      expect(
          DocumentTypeCheck.fromMap(
                  {'enabled': true, 'available': true, 'label': 'Other', 'confidence': 0.9})
              .isShown,
          isFalse);
      expect(
          DocumentTypeCheck.fromMap({'enabled': true, 'available': true, 'label': 'Blood'})
              .isShown,
          isFalse);
      expect(DocumentTypeCheck.hidden.isShown, isFalse);
    });
  });

  group('DatasetInfo', () {
    test('parses the server block and groups thousands', () {
      final d = DatasetInfo.tryParse({
        'name': 'MRAD (Unified Medical Dataset)',
        'classes': ['Blood', 'Health', 'TCGA'],
        'records_usable': 123367,
        'unique_patients': 110677,
        'train_records': 98000,
        'validation_records': 12000,
        'test_records': 13367,
      })!;
      expect(d.classes, ['Blood', 'Health', 'TCGA']);
      expect(DatasetInfo.group(d.usableRecords), '123,367');
      expect(DatasetInfo.group(999), '999');
      expect(DatasetInfo.group(1000), '1,000');
    });

    test('missing, empty or malformed data gives null, not a crash', () {
      expect(DatasetInfo.tryParse(null), isNull);
      expect(DatasetInfo.tryParse('x'), isNull);
      expect(DatasetInfo.tryParse(<String, dynamic>{}), isNull);
      expect(DatasetInfo.tryParse({'records_usable': 0}), isNull);
      expect(ModelPerformanceReport.fromMap(<String, dynamic>{}).dataset, isNull);
    });
  });

  group('DocumentTypeBadge', () {
    testWidgets('shows nothing when the feature is off', (tester) async {
      await tester.pumpWidget(_host(DocumentTypeBadge(
          reportId: 'r1', loader: (_) async => DocumentTypeCheck.hidden)));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('document-type-badge')), findsNothing);
    });

    testWidgets('shows nothing (and no error) when loading fails', (tester) async {
      await tester.pumpWidget(_host(DocumentTypeBadge(
          reportId: 'r1', loader: (_) async => throw Exception('offline'))));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('document-type-badge')), findsNothing);
      expect(tester.takeException(), isNull);
    });

    testWidgets('shows the hint, the score and an Experimental tag; tap explains', (tester) async {
      await tester.pumpWidget(_host(DocumentTypeBadge(
        reportId: 'r1',
        loader: (_) async => const DocumentTypeCheck(
            enabled: true, available: true, label: 'Blood', confidence: 0.87),
      )));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('document-type-badge')), findsOneWidget);
      expect(find.text('Looks like a blood-test report'), findsOneWidget);
      expect(find.text('Model score 87%'), findsOneWidget);
      expect(find.text('Experimental'), findsOneWidget);

      await tester.tap(find.byKey(const ValueKey('document-type-badge')));
      await tester.pumpAndSettle();
      expect(find.text('Document type check'), findsOneWidget);
      expect(find.textContaining('only a hint'), findsOneWidget);
      await tester.tap(find.text('Close'));
      await tester.pumpAndSettle();
      expect(find.text('Document type check'), findsNothing);
    });
  });
}
