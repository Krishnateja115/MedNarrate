import '../models/report_model.dart';
import '../repository/report_repository.dart';

class ReportService {
  ReportService._();

  static final ReportService instance = ReportService._();

  final ReportRepository _repository = ReportRepository.instance;

  List<ReportModel> getReports() {
    return _repository.getAllReports();
  }

  void addReport(ReportModel report) {
    _repository.addReport(report);
  }

  void updateReport(ReportModel report) {
    _repository.updateReport(report);
  }

  void deleteReport(String id) {
    _repository.deleteReport(id);
  }

  ReportModel? getReport(String id) {
    return _repository.getReportById(id);
  }

  List<ReportModel> searchReports(String query) {
    return _repository.searchReports(query);
  }

  List<ReportModel> favouriteReports() {
    return _repository.favouriteReports();
  }

  void toggleFavourite(String id) {
    final report = _repository.getReportById(id);

    if (report == null) return;

    _repository.updateReport(
      report.copyWith(
        isFavourite: !report.isFavourite,
      ),
    );
  }

  int totalReports() {
    return _repository.getAllReports().length;
  }

  int favouriteCount() {
    return _repository.favouriteReports().length;
  }

  void clearReports() {
    _repository.clearAllReports();
  }
}