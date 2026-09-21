import 'package:flutter/material.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/storage_service.dart';
import '../models/report_model.dart';

import '../../../core/services/api_models.dart';

class ReportDetailController extends ChangeNotifier {
  final ApiService _apiService = ApiService.instance;
  final StorageService _storageService = StorageService.instance;
  
  ReportModel? report;
  ReportAnalysisModel? analysis;
  ComparePreviousResult? comparison;
  bool isLoading = true;
  String? error;
  bool professionalMode = false;
  bool _disposed = false;

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
  
  Future<void> init(String reportId, ReportModel? initialReport) async {
    professionalMode = await _storageService.getProfessionalMode();
    if (initialReport != null) {
      report = initialReport;
      isLoading = false;
      if (!_disposed) notifyListeners();
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
      if (r.processingStatus == 'completed') {
        try {
          final resAnalysis = await _apiService.getReportAnalysis(reportId);
          analysis = resAnalysis;
          report = report!.copyWith(
            aiSummary: resAnalysis.patientSummary,
            clinicalSummary: resAnalysis.clinicianSummary,
            metrics: resAnalysis.structuredLabValues.map((v) => {
              'parameter': v.testName,
              'test_name': v.testName,
              'value': v.value,
              'unit': v.unit,
              'ref_low': v.refLow,
              'ref_high': v.refHigh,
              'flag': v.flag,
              'category': v.category,
            }).toList(),
          );
          try {
            comparison = await _apiService.comparePrevious(reportId);
          } catch (_) {}
        } catch (_) {}
      }
      error = null;
    } on ApiException catch (e) {
      if (report == null) error = e.message;
    } finally {
      isLoading = false;
      if (!_disposed) notifyListeners();
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
      if (!_disposed) notifyListeners();
    } catch (_) {}
  }

  Future<void> deleteReport() async {
    if (report == null) return;
    await _apiService.deleteReport(report!.id);
  }
}
