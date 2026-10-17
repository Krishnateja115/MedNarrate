import 'package:flutter/foundation.dart';
import '../../reports/models/report_model.dart';
import '../../../core/l10n/app_l10n.dart';
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
      if (!_disposed) error = appL10n.insightsFailedToLoad(e.toString());
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
        error = appL10n.insightsMax5;
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
      error = appL10n.insightsSelectAtLeast2;
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
        error = appL10n.insightsFailedCompare(e.toString());
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
