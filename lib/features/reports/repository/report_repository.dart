import '../models/report_model.dart';

class ReportRepository {
  ReportRepository._();

  static final ReportRepository instance =
      ReportRepository._();

  final List<ReportModel> _reports = [];

  List<ReportModel> getAllReports() {
    return List.unmodifiable(_reports);
  }

  void addReport(ReportModel report) {
    _reports.insert(0, report);
  }

  void updateReport(ReportModel report) {
    final index =
        _reports.indexWhere((e) => e.id == report.id);

    if (index != -1) {
      _reports[index] = report;
    }
  }

  void deleteReport(String id) {
    _reports.removeWhere((e) => e.id == id);
  }

  ReportModel? getReportById(String id) {
    try {
      return _reports.firstWhere(
        (e) => e.id == id,
      );
    } catch (_) {
      return null;
    }
  }

  List<ReportModel> searchReports(
    String query,
  ) {
    if (query.trim().isEmpty) {
      return getAllReports();
    }

    final q = query.toLowerCase();

    return _reports.where((report) {
      return report.title
              .toLowerCase()
              .contains(q) ||
          report.hospital
              .toLowerCase()
              .contains(q) ||
          report.reportType
              .toLowerCase()
              .contains(q) ||
          report.fileName
              .toLowerCase()
              .contains(q);
    }).toList();
  }

  List<ReportModel> favouriteReports() {
    return _reports
        .where((e) => e.isFavourite)
        .toList();
  }

  List<ReportModel> sortNewestFirst() {
    final reports =
        List<ReportModel>.from(_reports);

    reports.sort(
      (a, b) =>
          b.reportDate.compareTo(a.reportDate),
    );

    return reports;
  }

  List<ReportModel> sortOldestFirst() {
    final reports =
        List<ReportModel>.from(_reports);

    reports.sort(
      (a, b) =>
          a.reportDate.compareTo(b.reportDate),
    );

    return reports;
  }

  void clearAllReports() {
    _reports.clear();
  }
}