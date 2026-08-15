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

  InsightsController() {
    loadAvailableReports();
  }

  Future<void> loadAvailableReports() async {
    isLoading = true;
    error = null;
    notifyListeners();

    try {
      // Fetch user's reports. Assuming listReports gets all we need.
      availableReports = await _apiService.listReports(limit: 50);
      
      // Auto-select the first two if available to make testing easier
      if (availableReports.length >= 2) {
        selectedReportIds.add(availableReports[0].id);
        selectedReportIds.add(availableReports[1].id);
        await compareSelected();
      }
    } catch (e) {
      error = "Failed to load reports: ${e.toString()}";
    } finally {
      isLoading = false;
      notifyListeners();
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
      comparisonResult = await _apiService.compareReports(selectedReportIds.toList());
    } catch (e) {
      error = "Failed to generate comparison: ${e.toString()}";
      comparisonResult = null;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  void clearComparison() {
    selectedReportIds.clear();
    comparisonResult = null;
    error = null;
    notifyListeners();
  }
}
