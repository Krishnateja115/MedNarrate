import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/features/insights/screens/insights_controller.dart';

void main() {
  group('InsightsController Unit Tests', () {
    late InsightsController controller;

    setUp(() {
      // We instantiate directly; loadAvailableReports will fail gracefully
      controller = InsightsController();
    });

    tearDown(() {
      controller.dispose();
    });

    test('initial state has empty selection and no comparison result', () {
      expect(controller.selectedReportIds, isEmpty);
      expect(controller.comparisonResult, isNull);
    });

    test('toggleReportSelection adds a report ID', () {
      controller.toggleReportSelection('report-1');
      expect(controller.selectedReportIds, contains('report-1'));
    });

    test('toggleReportSelection removes a report ID if already selected', () {
      controller.toggleReportSelection('report-1');
      controller.toggleReportSelection('report-1');
      expect(controller.selectedReportIds, isNot(contains('report-1')));
    });

    test('toggleReportSelection allows up to 5 reports', () {
      for (int i = 1; i <= 5; i++) {
        controller.toggleReportSelection('report-$i');
      }
      expect(controller.selectedReportIds.length, equals(5));
    });

    test('toggleReportSelection does not add a 6th report', () {
      for (int i = 1; i <= 5; i++) {
        controller.toggleReportSelection('report-$i');
      }
      controller.toggleReportSelection('report-6');
      expect(controller.selectedReportIds.length, equals(5));
      expect(controller.error, contains('Maximum 5'));
    });

    test('clearComparison resets state', () {
      controller.toggleReportSelection('report-1');
      controller.toggleReportSelection('report-2');
      controller.clearComparison();
      expect(controller.selectedReportIds, isEmpty);
      expect(controller.comparisonResult, isNull);
      expect(controller.error, isNull);
    });

    test('compareSelected sets error when fewer than 2 reports selected', () async {
      controller.toggleReportSelection('report-1');
      await controller.compareSelected();
      expect(controller.error, contains('at least 2'));
    });

    test('compareSelected clears error before running', () async {
      // Put the controller in an error state first
      controller.toggleReportSelection('report-1');
      await controller.compareSelected(); // sets error
      expect(controller.error, isNotNull);

      // Add another report and try again - error should be cleared then possibly set by API failure
      controller.toggleReportSelection('report-2');
      await controller.compareSelected();
      // Either null (success) or a new API error - but the "at least 2" error should be gone
      expect(controller.error, isNot(contains('at least 2')));
    });
  });
}
