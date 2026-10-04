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

  bool isTranslating = false;
  TranslationModel? translation;
  String? translationLanguage;
  int _translationRequest = 0;
  String? _pendingLanguage;
  /// Translations already loaded during this screen session, keyed by language.
  /// Display-only memo: switching back to a loaded language re-uses it instead
  /// of showing a blocking spinner. Nothing here is persisted or modified.
  final Map<String, TranslationModel> _loadedTranslations = {};

  /// Language currently being fetched (null when idle).
  String? get pendingLanguage => _pendingLanguage;

  /// Language currently displayed ('en' when no translation is active).
  String get displayLanguage => translation?.language ?? 'en';
  final Future<TranslationModel> Function(String, String) _translateAnalysis;

  ReportDetailController({Future<TranslationModel> Function(String, String)? translateAnalysis})
      : _translateAnalysis = translateAnalysis ?? ApiService.instance.translateAnalysis;

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
  
  Future<void> init(String reportId, ReportModel? initialReport) async {
    final profMode = await _storageService.getProfessionalMode();
    if (_disposed) return;
    professionalMode = profMode;
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
      var r = await _apiService.getReport(reportId);
      if (_disposed) return;
      report = r;

      // Poll if report is currently processing or uploaded
      int attempts = 0;
      while ((r.processingStatus == 'processing' || r.processingStatus == 'uploaded') && attempts < 15) {
        await Future.delayed(const Duration(seconds: 2));
        if (_disposed) return;
        attempts++;
        try {
          r = await _apiService.getReport(reportId);
          report = r;
          if (!_disposed) notifyListeners();
        } catch (_) {
          break;
        }
      }

      if (r.processingStatus == 'completed') {
        try {
          final resAnalysis = await _apiService.getReportAnalysis(reportId);
          if (_disposed) return;
          analysis = resAnalysis;
          report = report!.copyWith(
            aiSummary: resAnalysis.patientSummary,
            translatedClinicalSummary: resAnalysis.translatedClinicianSummary,
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
            final comp = await _apiService.comparePrevious(reportId);
            if (_disposed) return;
            comparison = comp;
          } catch (_) {}
        } catch (analysisErr) {
          debugPrint('Error fetching report analysis: $analysisErr');
        }
      } else if (r.processingStatus == 'failed') {
        try {
          final status = await _apiService.getReportStatus(reportId);
          if (_disposed) return;
          error = status.errorReason ?? 'Report processing failed.';
        } catch (_) {}
      }
      error = null;
    } on ApiException catch (e) {
      if (!_disposed && report == null) error = e.message;
    } finally {
      if (!_disposed) {
        isLoading = false;
        notifyListeners();
      }
    }
  }

  Future<void> toggleFavourite() async {
    if (report == null) return;
    try {
      final updated = await _apiService.patchReport(
        report!.id,
        isFavourite: !report!.isFavourite,
      );
      if (_disposed) return;
      report = updated;
      notifyListeners();
    } catch (_) {}
  }

  Future<void> deleteReport() async {
    if (report == null) return;
    await _apiService.deleteReport(report!.id);
  }

  Future<void> translate(String languageCode) async {
    if (_disposed || report == null) return;
    if (isTranslating && _pendingLanguage == languageCode) return;
    final request = ++_translationRequest;
    _pendingLanguage = languageCode;
    if (languageCode == 'en') {
      translation = null;
      translationLanguage = 'en';
      isTranslating = false;
      _pendingLanguage = null;
      notifyListeners();
      return;
    }

    final cached = _loadedTranslations[languageCode];
    if (cached != null) {
      translation = cached;
      translationLanguage = cached.language;
      isTranslating = false;
      _pendingLanguage = null;
      notifyListeners();
      return;
    }

    isTranslating = true;
    notifyListeners();
    try {
      final t = await _translateAnalysis(report!.id, languageCode);
      if (_disposed) return;
      final valid = t.language == languageCode && t.patientSummary.trim().isNotEmpty;
      if (valid) _loadedTranslations[t.language] = t;
      if (request != _translationRequest) return;
      if (!valid) {
        throw const ApiException(502, 'Translation returned an unexpected language or empty report.');
      }
      translation = t;
      translationLanguage = t.language;
    } catch (_) {
      if (!_disposed && request == _translationRequest) rethrow;
    } finally {
      if (!_disposed && request == _translationRequest) {
        isTranslating = false;
        _pendingLanguage = null;
        notifyListeners();
      }
    }
  }
}
