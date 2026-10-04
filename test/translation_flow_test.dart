import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/api_models.dart';
import 'package:mednarrate/core/utils/helpers.dart';
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

  test('switching back to an already-loaded language is instant (no new request)', () async {
    final calls = <String>[];
    final controller = ReportDetailController(translateAnalysis: (_, language) async {
      calls.add(language);
      return translated(language, 'text-$language');
    })..report = report;
    await controller.translate('hi');
    await controller.translate('te');
    await controller.translate('en');
    expect(controller.translation, isNull);
    final back = controller.translate('hi');
    // Served synchronously from the in-memory memo: never enters loading state.
    expect(controller.isTranslating, isFalse);
    await back;
    expect(controller.translation!.language, 'hi');
    expect(controller.translation!.patientSummary, 'text-hi');
    expect(calls, ['hi', 'te']);
    controller.dispose();
  });

  test('selector can switch to a loaded language while another is loading', () async {
    final slow = Completer<TranslationModel>();
    final controller = ReportDetailController(translateAnalysis: (_, language) =>
        language == 'ml' ? slow.future : Future.value(translated(language, 'text-$language')))
      ..report = report;
    await controller.translate('hi');
    final pending = controller.translate('ml');
    expect(controller.pendingLanguage, 'ml');
    await controller.translate('hi');
    expect(controller.isTranslating, isFalse);
    expect(controller.displayLanguage, 'hi');
    slow.complete(translated('ml', 'text-ml'));
    await pending;
    expect(controller.displayLanguage, 'hi');
    // The finished Malayalam result is kept for an instant later switch.
    await controller.translate('ml');
    expect(controller.displayLanguage, 'ml');
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

  test('translated PDF sanitizer keeps every script; English sanitizer unchanged', () {
    for (final text in scripts.values) {
      final line = '### $text\n• MCV (MCV): 80.0 — $text (81.0 - 101.0).';
      final out = Helpers.sanitizePdfTextUnicode(line);
      expect(out, contains(text));
      expect(out, contains('(MCV)'));
      expect(out, contains('80.0'));
      expect(out.startsWith('#'), isFalse);
    }
    // Existing English/WinAnsi behaviour is preserved for English PDFs.
    expect(Helpers.sanitizePdfText('Hb • low'), 'Hb - low');
  });
}
