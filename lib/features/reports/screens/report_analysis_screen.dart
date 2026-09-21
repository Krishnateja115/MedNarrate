import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/api_models.dart';
import '../../../core/services/tts_service.dart';
import '../../../core/services/export_service.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/utils/report_polling.dart';
import '../../../core/routing/routes.dart';
import '../../../shared/widgets/skeleton_loader.dart';
import 'package:go_router/go_router.dart';
import 'package:mednarrate/l10n/app_localizations.dart';
import '../../../core/utils/markdown_formatter.dart';
import '../models/report_model.dart';
import '../widgets/clinical_view_tab.dart';
import 'package:shimmer/shimmer.dart';
import 'dart:async';

/// ReportAnalysisScreen — shows AI analysis results.
/// Handles polling (if not yet completed), failure with retry, and dual-mode summary toggle.
class ReportAnalysisScreen extends StatefulWidget {
  final String reportId;
  // Legacy support — old code passed a ReportModel
  final dynamic report;

  const ReportAnalysisScreen({super.key, required this.reportId, this.report});

  @override
  State<ReportAnalysisScreen> createState() => _ReportAnalysisScreenState();
}

class _ReportAnalysisScreenState extends State<ReportAnalysisScreen> {
  ReportAnalysisModel? _analysis;
  ReportModel? _report;
  String _status = 'loading';
  String? _errorReason;
  bool _clinicalView = false;
  bool _translating = false;
  bool _exporting = false;
  String? _translatedSummary;

  final TTSService _tts = TTSService.instance;

  @override
  void initState() {
    super.initState();
    _tts.init();
    _init();
  }

  @override
  void dispose() {
    _tts.stop();
    super.dispose();
  }

  Future<void> _init() async {
    try {
      if (widget.report is ReportModel) {
        _report = widget.report;
      } else {
        _report = await ApiService.instance.getReport(widget.reportId);
      }
      final status = await ApiService.instance.getReportStatus(widget.reportId);
      if (!mounted) return;
      if (status.processingStatus == 'completed') {
        _loadAnalysis();
      } else if (status.processingStatus == 'failed') {
        setState(() { _status = 'failed'; _errorReason = status.errorReason; });
      } else {
        // Poll
        setState(() => _status = 'processing');
        _startPolling();
      }
    } catch (e) {
      if (mounted) setState(() { _status = 'failed'; _errorReason = e.toString(); });
    }
  }

  void _startPolling() {
    pollReportStatus(widget.reportId).listen((status) {
      if (!mounted) return;
      if (status.processingStatus == 'completed') {
        _loadAnalysis();
      } else if (status.processingStatus == 'failed') {
        setState(() { _status = 'failed'; _errorReason = status.errorReason; });
      }
    });
  }

  Future<void> _loadAnalysis() async {
    try {
      _report ??= await ApiService.instance.getReport(widget.reportId);
      final analysis = await ApiService.instance.getReportAnalysis(widget.reportId);
      if (!mounted) return;
      setState(() { _analysis = analysis; _status = 'completed'; });
    } on ApiException catch (e) {
      if (mounted) setState(() { _status = 'failed'; _errorReason = e.message; });
    }
  }

  Future<void> _translate() async {
    if (_translating) return;
    setState(() => _translating = true);
    try {
      final lang = await _getUserLang();
      final t = await ApiService.instance.translateAnalysis(widget.reportId, lang);
      if (mounted) setState(() => _translatedSummary = t.patientSummary);
    } on ApiException catch (e) {
      if (mounted) Helpers.showError(context, e.message);
    } finally {
      if (mounted) setState(() => _translating = false);
    }
  }

  Future<String> _getUserLang() async {
    try {
      final user = await ApiService.instance.getMe();
      return user.preferredLanguage;
    } catch (_) {
      return 'hi';
    }
  }

  Future<void> _retry() async {
    setState(() { _status = 'processing'; _errorReason = null; });
    try {
      await ApiService.instance.processReport(widget.reportId, force: true);
      _startPolling();
    } on ApiException catch (e) {
      if (mounted) setState(() { _status = 'failed'; _errorReason = e.message; });
    }
  }

  Color _flagColor(String flag) => Helpers.flagColor(flag);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
        title: Text(AppLocalizations.of(context)?.aiAnalysis ?? 'AI Analysis'),
        actions: [
          if (_status == 'completed')
            IconButton(
              onPressed: () => context.push(Routes.aiChat, extra: widget.reportId),
              icon: Icon(Icons.chat_bubble_outline),
              tooltip: 'Ask AI about this report',
            ),
        ],
      ),
      body: switch (_status) {
        'loading' => Padding(padding: EdgeInsets.all(20), child: SkeletonAnalysis()),
        'processing' => _buildProcessing(),
        'failed' => _buildFailed(),
        _ => _buildCompleted(),
      },
      bottomNavigationBar: _status == 'completed' ? _buildBottomBar() : null,
    );
  }

  Widget _buildProcessing() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Shimmer.fromColors(
            baseColor: AppColors.primary,
            highlightColor: AppColors.primary.withOpacity(0.3),
            child: Icon(Icons.auto_awesome, size: 64),
          ),
          SizedBox(height: 28),
          Text(AppLocalizations.of(context)?.analyzingYourReport ?? 'Analyzing your report',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.onSurface)),
          SizedBox(height: 16),
          const _ProcessingStages(),
        ],
      ),
    );
  }

  Widget _buildFailed() {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, color: Colors.red, size: 60),
            SizedBox(height: 16),
            Text(AppLocalizations.of(context)?.analysisFailed ?? 'Analysis Failed', style: TextStyle(fontSize: 22, color: Theme.of(context).colorScheme.onSurface, fontWeight: FontWeight.bold)),
            SizedBox(height: 12),
            Text(_errorReason ?? 'An unknown error occurred.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70))),
            SizedBox(height: 28),
            FilledButton.icon(
              onPressed: _retry,
              icon: Icon(Icons.refresh),
              label: Text(AppLocalizations.of(context)?.retryAnalysis ?? 'Retry Analysis'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCompleted() {
    final a = _analysis!;
    final activeSummary = _translatedSummary ??
        (_clinicalView ? a.clinicianSummary : a.patientSummary) ?? '';

    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 90),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Dual-mode toggle ──────────────────────────────────────────
          Container(
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              children: [
                Expanded(child: _modeTab('For You', !_clinicalView, () => setState(() => _clinicalView = false))),
                Expanded(child: _modeTab('Clinical View', _clinicalView, () => setState(() => _clinicalView = true))),
              ],
            ),
          ),
          SizedBox(height: 16),
          
          // ── Verification Badge ─────────────────────────────────────────
          _buildVerificationBadge(a.verificationStatus),
          
          SizedBox(height: 16),

          // ── Summary card with TTS ─────────────────────────────────────
          Row(
            children: [
              Expanded(child: Text(AppLocalizations.of(context)?.summary ?? 'Summary',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.onSurface))),
              ValueListenableBuilder<TtsState>(
                valueListenable: _tts.stateNotifier,
                builder: (context, ttsState, child) => IconButton(
                  onPressed: () {
                    if (ttsState == TtsState.playing) {
                      _tts.stop();
                    } else {
                      _tts.speak(activeSummary);
                    }
                  },
                  icon: Icon(
                    ttsState == TtsState.playing ? Icons.stop_circle : Icons.volume_up_outlined,
                    color: ttsState == TtsState.playing ? Colors.redAccent : AppColors.primary,
                  ),
                  tooltip: ttsState == TtsState.playing ? 'Stop reading' : 'Read aloud',
                ),
              ),
            ],
          ),
          SizedBox(height: 8),
          _card(
            child: activeSummary.isEmpty
                ? Text('No summary available.', style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)))
                : MarkdownFormatter.formatText(context, activeSummary),
          ),
          SizedBox(height: 12),

          // Translate button
          if (!_clinicalView && a.translationAvailable && _translatedSummary == null)
            _card(
              child: Row(
                children: [
                  Icon(Icons.translate, color: Colors.blue),
                  SizedBox(width: 12),
                  Expanded(child: Text(AppLocalizations.of(context)?.translatedVersionAvailable ?? 'Translated version available',
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)))),
                  TextButton(onPressed: _translate, child: Text(AppLocalizations.of(context)?.load ?? 'Load')),
                ],
              ),
            ),
          if (!_clinicalView && !a.translationAvailable && _translatedSummary == null)
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                onPressed: _translating ? null : _translate,
                icon: _translating
                    ? SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : Icon(Icons.translate),
                label: Text(_translating ? 'Translating…' : 'Translate to preferred language'),
              ),
            ),

          SizedBox(height: 24),

          _clinicalView 
            ? ClinicalViewTab(
                report: _report!,
                analysis: a,
              )
            : _buildPatientFriendlyFindings(a),
        ],
      ),
    );
  }

  Widget _buildPatientFriendlyFindings(ReportAnalysisModel a) {
    int normalCount = a.structuredLabValues.where((l) => l.flag.toLowerCase() == 'normal').length;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (a.abnormalFindings.isNotEmpty) ...[
          _sectionTitle('Abnormal Findings'),
          _buildAbnormalFindings(a),
          SizedBox(height: 20),
        ],
        if (normalCount > 0)
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Text(
              'Everything else was within the normal range ($normalCount results).',
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
      ],
    );
  }


  Widget _buildBottomBar() {
    final a = _analysis!;
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(16, 8, 16, 12),
        child: Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _exporting ? null : () async {
                  setState(() => _exporting = true);
                  try {
                    await ExportService.instance.shareSummaryPdf(
                      analysis: a,
                      reportTitle: 'Report Analysis',
                      reportDate: a.processedAt?.toLocal().toString().split(' ').first ?? '',
                    );
                  } catch (e) {
                    if (mounted) Helpers.showError(context, 'Export failed: $e');
                  } finally {
                    if (mounted) setState(() => _exporting = false);
                  }
                },
                icon: _exporting
                    ? SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : Icon(Icons.picture_as_pdf_outlined),
                label: Text(_exporting ? 'Exporting…' : 'Export PDF'),
                style: OutlinedButton.styleFrom(
                  padding: EdgeInsets.symmetric(vertical: 14),
                  side: BorderSide(color: AppColors.primary),
                  foregroundColor: AppColors.primary,
                ),
              ),
            ),
            SizedBox(width: 12),
            Expanded(
              child: FilledButton.icon(
                onPressed: () => ExportService.instance.printSummary(
                  analysis: a,
                  reportTitle: 'Report Analysis',
                  reportDate: a.processedAt?.toLocal().toString().split(' ').first ?? '',
                ),
                icon: Icon(Icons.print_outlined),
                label: Text(AppLocalizations.of(context)?.printPreview ?? 'Print Preview'),
                style: FilledButton.styleFrom(padding: EdgeInsets.symmetric(vertical: 14)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _modeTab(String label, bool active, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: Duration(milliseconds: 200),
        margin: EdgeInsets.all(4),
        padding: EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: active ? AppColors.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(label,
            textAlign: TextAlign.center,
            style: TextStyle(
                color: active ? Theme.of(context).colorScheme.onSurface : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54),
                fontWeight: active ? FontWeight.bold : FontWeight.normal)),
      ),
    );
  }

  Widget _sectionTitle(String title) => Padding(
    padding: EdgeInsets.only(bottom: 12, top: 8),
    child: Text(title, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.onSurface)),
  );



  int _flagSeverity(String flag) {
    switch (flag.toLowerCase()) {
      case 'critical':
        return 4;
      case 'abnormal':
      case 'high':
        return 3;
      case 'low':
      case 'moderate':
      case 'borderline':
        return 2;
      case 'normal':
        return 1;
      default:
        return 0;
    }
  }

  Widget _buildAbnormalFindings(ReportAnalysisModel a) {
    // Deduplicate findings by name + flag
    final seen = <String>{};
    final uniqueFindings = <Map<String, dynamic>>[];
    for (var f in a.abnormalFindings) {
      final name = f['test_name']?.toString().trim() ?? '';
      final flag = f['flag']?.toString().trim().toLowerCase() ?? '';
      final key = '$name-$flag';
      if (!seen.contains(key) && name.isNotEmpty) {
        seen.add(key);
        uniqueFindings.add(f);
      }
    }

    // Sort decreasing severity: critical/abnormal/high first, then low/moderate, then normal
    uniqueFindings.sort((x, y) {
      final sevX = _flagSeverity(x['flag']?.toString() ?? '');
      final sevY = _flagSeverity(y['flag']?.toString() ?? '');
      if (sevY != sevX) return sevY.compareTo(sevX);
      return (x['test_name']?.toString() ?? '').compareTo(y['test_name']?.toString() ?? '');
    });

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: uniqueFindings.map((f) {
        final name = f['test_name']?.toString() ?? '';
        final flagStr = f['flag']?.toString().toLowerCase() ?? 'abnormal';
        final color = _flagColor(flagStr);
        final val = f['value'] != null ? '${f['value']}${f['unit'] != null ? ' ${f['unit']}' : ''}'.trim() : '';
        final sources = a.evidenceSources
            .where((e) => e.finding == name)
            .expand((e) => e.sources)
            .toSet()
            .toList();

        return Container(
          padding: EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: color.withValues(alpha: 0.35), width: 1),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                ),
              ),
              SizedBox(width: 6),
              Text(
                name,
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
              if (val.isNotEmpty) ...[
                SizedBox(width: 4),
                Text(
                  val,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.8),
                    fontWeight: FontWeight.w500,
                    fontSize: 11,
                  ),
                ),
              ],
              if (flagStr != 'normal' && flagStr.isNotEmpty) ...[
                SizedBox(width: 5),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 4, vertical: 1.5),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    flagStr.toUpperCase(),
                    style: TextStyle(
                      color: color,
                      fontSize: 8.5,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.4,
                    ),
                  ),
                ),
              ],
              if (sources.isNotEmpty) ...[
                SizedBox(width: 5),
                Tooltip(
                  message: 'Sources: ${sources.join(', ')}',
                  child: Icon(Icons.info_outline, size: 12, color: color.withValues(alpha: 0.7)),
                ),
              ],
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildVerificationBadge(String? status) {
    if (status == null || status.isEmpty || status == 'pending' || status == 'unverified') {
      return SizedBox.shrink(); // Don't clutter UI if not yet verified
    }
    
    IconData icon;
    Color color;
    String label;
    
    switch (status) {
      case 'verified':
        icon = Icons.verified_user;
        color = Colors.green;
        label = 'AI Fact-Checked & Verified';
        break;
      case 'needs_correction':
        icon = Icons.warning_amber_rounded;
        color = Colors.orange;
        label = 'Summary Contains Minor Inaccuracies';
        break;
      case 'hallucination_detected':
        icon = Icons.error_outline;
        color = Colors.red;
        label = 'Critical Inaccuracy Detected';
        break;
      default:
        return SizedBox.shrink();
    }
    
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 16),
          SizedBox(width: 8),
          Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _card({required Widget child}) => Container(
    width: double.infinity,
    margin: EdgeInsets.only(bottom: 12),
    padding: EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: Theme.of(context).cardColor,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: AppColors.border, width: 1),
    ),
    child: child,
  );
}
class _ProcessingStages extends StatefulWidget {
  const _ProcessingStages();
  @override
  State<_ProcessingStages> createState() => _ProcessingStagesState();
}

class _ProcessingStagesState extends State<_ProcessingStages> with SingleTickerProviderStateMixin {
  static const _stages = [
    'Reading your document…',
    'Extracting lab values…',
    'Cross-referencing reference ranges…',
    'Running AI analysis…',
    'Preparing your summary…',
  ];
  int _index = 0;
  late final Timer _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      if (mounted) setState(() => _index = (_index + 1) % _stages.length);
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 400),
      transitionBuilder: (child, animation) => FadeTransition(
        opacity: animation,
        child: SlideTransition(
          position: Tween<Offset>(begin: const Offset(0, 0.2), end: Offset.zero).animate(animation),
          child: child,
        ),
      ),
      child: Text(
        _stages[_index],
        key: ValueKey(_index),
        style: TextStyle(fontSize: 14, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.75)),
      ),
    );
  }
}
