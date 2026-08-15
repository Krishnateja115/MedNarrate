import 'package:flutter/material.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/storage_service.dart';
import '../models/report_model.dart';

class ReportDetailController extends ChangeNotifier {
  final ApiService _apiService = ApiService.instance;
  final StorageService _storageService = StorageService.instance;
  
  ReportModel? report;
  bool isLoading = true;
  String? error;
  bool professionalMode = false;
  
  Future<void> init(String reportId, ReportModel? initialReport) async {
    professionalMode = await _storageService.getProfessionalMode();
    if (initialReport != null) {
      report = initialReport;
      isLoading = false;
      notifyListeners();
      // Still fetch latest in background
      _fetchLatest(reportId);
    } else {
      await _fetchLatest(reportId);
    }
  }

  Future<void> _fetchLatest(String reportId) async {
    try {
      final r = await _apiService.getReport(reportId);
      report = r;
      error = null;
    } on ApiException catch (e) {
      if (report == null) error = e.message;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> toggleFavourite() async {
    if (report == null) return;
    try {
      final updated = await _apiService.patchReport(
        report!.id,
        isFavourite: !report!.isFavourite,
      );
      report = updated;
      notifyListeners();
    } catch (_) {}
  }

  Future<void> deleteReport() async {
    if (report == null) return;
    await _apiService.deleteReport(report!.id);
  }
}
