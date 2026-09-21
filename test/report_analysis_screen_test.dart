import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/features/reports/screens/report_analysis_screen.dart';
import 'package:mednarrate/features/reports/models/report_model.dart';
import 'package:mednarrate/core/services/api_models.dart';
import 'package:mednarrate/core/services/api_service.dart';

class MockApiService implements ApiService {
  @override
  Future<ReportModel> getReport(String id) async {
    return ReportModel(
      id: id,
      title: 'Mock Test Report',
      hospital: 'General Hospital',
      reportType: 'CBC',
      reportDate: DateTime.now(),
      fileName: 'report.pdf',
      filePath: '/mock/path/report.pdf',
      fileType: 'application/pdf',
      extractedText: 'Mock extracted text',
      processingStatus: 'completed',
      isFavourite: false,
      uploadedAt: DateTime.now(),
      metrics: [],
    );
  }

  @override
  Future<ReportAnalysisModel> getReportAnalysis(String id) async {
    return ReportAnalysisModel(
      id: 'analysis_123',
      reportId: id,
      patientSummary: '### Patient Summary\n**Mock Patient Summary** with some markdown.',
      clinicianSummary: '### Clinical Summary\n**Mock Clinical Summary** with markdown.',
      structuredLabValues: [
        LabValue(testName: 'Hemoglobin', value: 12.0, unit: 'g/dL', refLow: 13.0, refHigh: 17.0, flag: 'LOW')
      ],
      entities: [],
      medications: [],
      abnormalFindings: [
        {'test_name': 'Hemoglobin', 'value': 12.0, 'unit': 'g/dL', 'flag': 'LOW'}
      ],
      evidenceSources: [],
      processedAt: DateTime.now(),
    );
  }

  @override
  Future<ReportStatus> getReportStatus(String id) async {
    return ReportStatus(
      processingStatus: 'completed',
    );
  }

  @override
  noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  setUp(() {
    ApiService.instance = MockApiService();
  });

  Widget buildTestWidget() {
    return MaterialApp(
      home: Scaffold(
        body: ReportAnalysisScreen(reportId: 'rep_123'),
      ),
    );
  }

  testWidgets('ReportAnalysisScreen renders formatted markdown and switches views correctly', (WidgetTester tester) async {
    await tester.pumpWidget(buildTestWidget());

    // Wait for Futures (getReport, getReportAnalysis) to resolve
    await tester.pumpAndSettle();

    // Now it should show the completed view in "For You" mode (patient mode)
    // We should NOT see raw markdown like "### Patient Summary" or "**Mock Patient Summary**"
    // Instead we should see the parsed text.
    final rawTextFinder = find.byWidgetPredicate((widget) {
      if (widget is Text) {
        final text = widget.data ?? widget.textSpan?.toPlainText() ?? '';
        return text.contains('### Patient Summary') || text.contains('**Mock Patient Summary**');
      }
      return false;
    });
    
    expect(rawTextFinder, findsNothing, reason: 'Raw markdown symbols should not be in the rendered Text widgets');
    
    // We should see "For You" specific widgets
    debugDumpApp();
    // Wait for Futures (getReport, getReportAnalysis) to resolve
    await tester.pumpAndSettle();
    
    expect(find.textContaining('Failed', skipOffstage: false), findsNothing, reason: 'Screen should not be in failed state');
    expect(find.text('Abnormal Findings', skipOffstage: false), findsOneWidget);
    
    // "Clinical View" specific widgets should NOT be visible
    expect(find.text('Clinical Executive Summary'), findsNothing);
    
    // Switch to Clinical View
    await tester.tap(find.text('Clinical View'));
    await tester.pumpAndSettle();
    
    // "For You" specific widgets should disappear or change
    // Wait, Abnormal Findings might still be there in ClinicalView, but Clinical Executive Summary will definitely appear
    expect(find.text('Clinical Executive Summary'), findsOneWidget);
    
    // Also no raw markdown in Clinical View
    final rawClinicalFinder = find.byWidgetPredicate((widget) {
      if (widget is Text) {
        final text = widget.data ?? widget.textSpan?.toPlainText() ?? '';
        return text.contains('### Clinical Summary') || text.contains('**Mock Clinical Summary**');
      }
      return false;
    });
    expect(rawClinicalFinder, findsNothing, reason: 'Raw markdown symbols should not be in the rendered Text widgets in Clinical View');
  });
}
