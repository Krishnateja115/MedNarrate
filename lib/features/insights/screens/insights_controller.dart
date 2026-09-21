import 'package:flutter/foundation.dart';
import '../../reports/models/report_model.dart';
import '../../../core/services/api_service.dart';
import '../../../models/comparison_models.dart';

class InsightsController extends ChangeNotifier {
  final ApiService _apiService = ApiService.instance;

  Set<String> selectedReportIds = {};
  ReportComparisonResult? comparisonResult;
  bool isLoading = false;
  String? error;
  List<ReportModel> availableReports = [];
  bool _disposed = false;

  InsightsController() {
    loadAvailableReports();
  }

  Future<void> loadAvailableReports() async {
    if (_disposed) return;
    isLoading = true;
    error = null;
    notifyListeners();

    try {
      // Fetch user's reports. Assuming listReports gets all we need.
      final reports = await _apiService.listReports(limit: 50);
      if (_disposed) return;
      availableReports = reports;
      
      // Auto-select the first two if available to make testing easier
      if (availableReports.length >= 2) {
        selectedReportIds.add(availableReports[0].id);
        selectedReportIds.add(availableReports[1].id);
        await compareSelected();
      }
    } catch (e) {
      if (!_disposed) error = "Failed to load reports: ${e.toString()}";
    } finally {
      if (!_disposed) {
        isLoading = false;
        notifyListeners();
      }
    }
  }

  void toggleReportSelection(String reportId) {
    if (selectedReportIds.contains(reportId)) {
      selectedReportIds.remove(reportId);
    } else {
      if (selectedReportIds.length < 5) {
        selectedReportIds.add(reportId);
      } else {
        error = "Maximum 5 reports can be selected for comparison.";
        notifyListeners();
        return;
      }
    }
    
    // Clear the current comparison result because selection changed
    comparisonResult = null;
    notifyListeners();
  }

  Future<void> compareSelected() async {
    if (selectedReportIds.length < 2) {
      error = "Select at least 2 reports to compare.";
      notifyListeners();
      return;
    }

    isLoading = true;
    error = null;
    notifyListeners();

    try {
      final comp = await _apiService.compareReports(selectedReportIds.toList());
      if (_disposed) return;
      comparisonResult = comp;
    } catch (e) {
      if (!_disposed) {
        error = "Failed to generate comparison: ${e.toString()}";
        comparisonResult = null;
      }
    } finally {
      if (!_disposed) {
        isLoading = false;
        notifyListeners();
      }
    }
  }

  void clearComparison() {
    selectedReportIds.clear();
    comparisonResult = null;
    error = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
