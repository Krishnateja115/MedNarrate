import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/api_models.dart';
import 'package:mednarrate/core/utils/report_polling.dart';

void main() {
  test('polling waits for the backend to finish despite slow processing',
      () async {
    var calls = 0;
    final statuses = await pollReportStatus(
      'report-1',
      interval: Duration.zero,
      getStatus: (_) async {
        calls++;
        return ReportStatus(
            processingStatus: calls < 105 ? 'processing' : 'completed');
      },
    ).toList();

    expect(calls, 105);
    expect(statuses.last.processingStatus, 'completed');
    expect(statuses.where((s) => s.processingStatus == 'failed'), isEmpty);
  });

  test('temporary network error never turns into a failed report', () async {
    var calls = 0;
    final statuses = await pollReportStatus(
      'report-2',
      interval: Duration.zero,
      getStatus: (_) async {
        calls++;
        if (calls == 1) throw Exception('connection interrupted');
        return const ReportStatus(processingStatus: 'completed');
      },
    ).toList();

    expect(
        statuses.map((s) => s.processingStatus), ['processing', 'completed']);
    expect(statuses.first.errorReason, contains('connection interrupted'));
  });
}
