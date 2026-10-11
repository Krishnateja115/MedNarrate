import 'dart:async';
import '../services/api_service.dart';
import '../services/api_models.dart';

/// Polls [ApiService.getReportStatus] on [interval] and yields each [ReportStatus].
/// Stops only when the backend reports "completed" or "failed". A slow report
/// or a temporary connection problem must not be presented as analysis failure.
Stream<ReportStatus> pollReportStatus(
  String reportId, {
  Duration interval = const Duration(seconds: 3),
  Future<ReportStatus> Function(String)? getStatus,
}) async* {
  final fetchStatus = getStatus ?? ApiService.instance.getReportStatus;

  while (true) {
    try {
      final status = await fetchStatus(reportId);
      yield status;
      if (status.processingStatus == 'completed' ||
          status.processingStatus == 'failed') {
        return;
      }
    } catch (e) {
      yield ReportStatus(
          processingStatus: 'processing', errorReason: e.toString());
    }
    await Future<void>.delayed(interval);
  }
}
