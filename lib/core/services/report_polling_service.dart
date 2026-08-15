import 'dart:async';
import 'api_service.dart';

enum ReportStatus { processing, completed, failed }

class ReportPollingService {
  ReportPollingService._();
  static final ReportPollingService instance = ReportPollingService._();

  Stream<ReportStatus> pollReportStatus(String reportId) {
    final controller = StreamController<ReportStatus>();
    Timer? timer;
    int ticks = 0;
    const maxTicks = 100; // 5 minutes at 3 seconds per tick

    void checkStatus() async {
      if (controller.isClosed) return;
      
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
          ticks++;
          if (ticks >= maxTicks) {
            controller.add(ReportStatus.failed);
            timer?.cancel();
            controller.close();
          }
        }
      } catch (e) {
        // Assume failure on recurring network error after a few tries
        ticks++;
        if (ticks >= maxTicks) {
          controller.add(ReportStatus.failed);
          timer?.cancel();
          controller.close();
        }
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
