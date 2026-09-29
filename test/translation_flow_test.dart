import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/api_models.dart';
import 'package:mednarrate/core/services/translated_report_pdf.dart';
import 'package:mednarrate/features/reports/controllers/report_detail_controller.dart';
import 'package:mednarrate/features/reports/models/report_model.dart';
import 'package:mednarrate/features/reports/widgets/patient_view_tab.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

final report = ReportModel(
  id: 'synthetic-report', title: 'Blood report', hospital: '',
  reportDate: DateTime(2026, 9, 28), fileName: 'synthetic.pdf',
  filePath: '', fileType: 'pdf', reportType: 'blood', extractedText: '',
  processingStatus: 'completed', isFavourite: false, uploadedAt: DateTime(2026),
);
const analysis = ReportAnalysisModel(
  id: 'analysis', reportId: 'synthetic-report',
  structuredLabValues: [LabValue(testName: 'Hemoglobin', value: 10.2, unit: 'g/dL', refLow: 12, refHigh: 16, flag: 'low')],
  entities: [], abnormalFindings: [], medications: [], evidenceSources: [],
  patientSummary: 'Original English summary',
);
TranslationModel translated(String language, [String text = 'మీ రక్త పరీక్ష నివేదిక']) => TranslationModel(
  language: language, patientSummary: text, findingsJson: const [],
  doctorDiscussionPoints: [text], schemaVersion: 3,
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('latest selected language wins over a slower response', () async {
    final requests = <String, Completer<TranslationModel>>{};
    final controller = ReportDetailController(translateAnalysis: (id, language) {
      expect(id, report.id);
      return (requests[language] = Completer<TranslationModel>()).future;
    })..report = report;
    final te = controller.translate('te');
    final ta = controller.translate('ta');
    requests['ta']!.complete(translated('ta', 'உங்கள் இரத்த பரிசோதனை அறிக்கை'));
    await ta;
    requests['te']!.complete(translated('te'));
    await te;
    expect(controller.translationLanguage, 'ta');
    expect(controller.isTranslating, isFalse);
    controller.dispose();
  });

  test('English cancels display of an in-flight translation', () async {
    final response = Completer<TranslationModel>();
    final controller = ReportDetailController(translateAnalysis: (_, __) => response.future)
      ..report = report..analysis = analysis;
    final pending = controller.translate('te');
    await controller.translate('en');
    response.complete(translated('te'));
    await pending;
    expect(controller.translation, isNull);
    expect(controller.analysis!.patientSummary, 'Original English summary');
    expect(controller.isTranslating, isFalse);
    controller.dispose();
  });

  test('duplicate requests are suppressed and failures finish loading', () async {
    var calls = 0;
    final response = Completer<TranslationModel>();
    final controller = ReportDetailController(translateAnalysis: (_, __) {
      calls++;
      return response.future;
    })..report = report;
    final pending = controller.translate('te');
    final expectation = expectLater(pending, throwsStateError);
    await controller.translate('te');
    expect(calls, 1);
    response.completeError(StateError('Unavailable'));
    await expectation;
    expect(controller.isTranslating, isFalse);
    expect(controller.translation, isNull);
    controller.dispose();
  });

  test('unexpected response language does not replace the original', () async {
    final controller = ReportDetailController(translateAnalysis: (_, __) async => translated('hi'))
      ..report = report;
    await expectLater(controller.translate('te'), throwsException);
    expect(controller.translation, isNull);
    expect(controller.isTranslating, isFalse);
    controller.dispose();
  });

  const scripts = {
    'te': 'మీ రక్త పరీక్ష నివేదిక', 'ta': 'உங்கள் இரத்த பரிசோதனை அறிக்கை',
    'kn': 'ನಿಮ್ಮ ರಕ್ತ ಪರೀಕ್ಷಾ ವರದಿ', 'ml': 'നിങ്ങളുടെ രക്ത പരിശോധന റിപ്പോർട്ട്',
    'hi': 'आपकी रक्त परीक्षण रिपोर्ट',
  };
  for (final entry in scripts.entries) {
    testWidgets('${entry.key}: Unicode response renders the patient body', (tester) async {
      tester.view.physicalSize = const Size(1200, 2200);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final wire = utf8.encode(jsonEncode({
        'language': entry.key, 'patient_summary': entry.value,
        'findings_json': [], 'doctor_discussion_points': [entry.value], 'ui_labels': {},
      }));
      final model = TranslationModel.fromMap(jsonDecode(utf8.decode(wire)) as Map<String, dynamic>);
      await tester.pumpWidget(MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Scaffold(body: PatientViewTab(report: report, analysis: analysis, translation: model)),
      ));
      await tester.pumpAndSettle();
      expect(find.textContaining(entry.value, findRichText: true), findsWidgets);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('translated PDF accepts all scripts and long reports', (tester) async {
    await tester.runAsync(() async {
      final body = List.generate(90, (i) => '${scripts.values.join(' ')} 10.2 g/dL').join('\n');
      final doc = await buildTranslatedReportPdf(
        analysis: analysis, translation: translated('te', body),
        reportTitle: report.title, reportDate: '2026-09-28',
      );
      final bytes = await doc.save();
      expect(ascii.decode(bytes.take(4).toList()), '%PDF');
      expect(bytes.length, greaterThan(1000));
    });
  });
}
