import 'dart:async';
import '../services/api_service.dart';
import '../services/api_models.dart';

/// Polls [ApiService.getReportStatus] on [interval] and yields each [ReportStatus].
/// Automatically stops when [processingStatus] is "completed" or "failed",
/// or after [timeout] elapses.
Stream<ReportStatus> pollReportStatus(
  String reportId, {
  Duration interval = const Duration(seconds: 3),
  Duration timeout = const Duration(minutes: 2),
}) async* {
  final deadline = DateTime.now().add(timeout);

  while (DateTime.now().isBefore(deadline)) {
    try {
      final status = await ApiService.instance.getReportStatus(reportId);
      yield status;
      if (status.processingStatus == 'completed' ||
          status.processingStatus == 'failed') {
        return;
      }
    } catch (e) {
      // On error, yield a synthetic failed status so callers can handle it
      yield ReportStatus(processingStatus: 'failed', errorReason: e.toString());
      return;
    }
    await Future<void>.delayed(interval);
  }

  // Timeout reached
  yield ReportStatus(
      processingStatus: 'failed', errorReason: 'Polling timed out after 2 minutes');
}
