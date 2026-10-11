import 'dart:async';
import 'api_service.dart';

enum ReportStatus { processing, completed, failed }

class ReportPollingService {
  ReportPollingService._();
  static final ReportPollingService instance = ReportPollingService._();

  Stream<ReportStatus> pollReportStatus(String reportId) {
    final controller = StreamController<ReportStatus>();
    Timer? timer;
    bool isChecking = false;

    void checkStatus() async {
      if (controller.isClosed || isChecking) return;
      isChecking = true;

      try {
        final report = await ApiService.instance.getReport(reportId);

        if (report.processingStatus == 'completed') {
          controller.add(ReportStatus.completed);
          timer?.cancel();
          controller.close();
        } else if (report.processingStatus == 'failed') {
          controller.add(ReportStatus.failed);
          timer?.cancel();
          controller.close();
        } else {
          controller.add(ReportStatus.processing);
        }
      } catch (e) {
        // Keep checking; only the backend can declare analysis failure.
        if (!controller.isClosed) {
          controller.add(ReportStatus.processing);
        }
      } finally {
        isChecking = false;
      }
    }

    controller.onListen = () {
      checkStatus();
      timer = Timer.periodic(const Duration(seconds: 3), (_) {
        checkStatus();
      });
    };

    controller.onCancel = () {
      timer?.cancel();
    };

    return controller.stream;
  }
}
