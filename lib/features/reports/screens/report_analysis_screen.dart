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
        title: Text(AppLocalizations.of(context)!.aiAnalysis),
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
          SizedBox(
            width: 56, height: 56,
            child: CircularProgressIndicator(strokeWidth: 3, color: AppColors.primary),
          ),
          SizedBox(height: 28),
          Text(AppLocalizations.of(context)!.analyzingYourReport,
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: Theme.of(context).colorScheme.onSurface)),
          SizedBox(height: 10),
          Text(AppLocalizations.of(context)!.aiReadingDocument,
              textAlign: TextAlign.center,
              style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 13)),
          SizedBox(height: 32),
          _processingStep('Reading document text', true),
          _processingStep('Extracting medical data', true),
          _processingStep('Running AI analysis', false),
        ],
      ),
    );
  }

  Widget _processingStep(String label, bool done) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 6),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(done ? Icons.check_circle : Icons.radio_button_unchecked,
            color: done ? Color(0xFF00C48C) : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.24), size: 18),
        SizedBox(width: 10),
        Text(label, style: TextStyle(color: done ? Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70) : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.30), fontSize: 13)),
      ]),
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
            Text(AppLocalizations.of(context)!.analysisFailed, style: TextStyle(fontSize: 22, color: Theme.of(context).colorScheme.onSurface, fontWeight: FontWeight.bold)),
            SizedBox(height: 12),
            Text(_errorReason ?? 'An unknown error occurred.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70))),
            SizedBox(height: 28),
            FilledButton.icon(
              onPressed: _retry,
              icon: Icon(Icons.refresh),
              label: Text(AppLocalizations.of(context)!.retryAnalysis),
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
          SizedBox(height: 24),

          // ── Summary card with TTS ─────────────────────────────────────
          Row(
            children: [
              Expanded(child: Text(AppLocalizations.of(context)!.summary,
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
            child: Text(activeSummary.isEmpty ? 'No summary available.' : activeSummary,
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70), height: 1.6)),
          ),
          SizedBox(height: 12),

          // Translate button
          if (!_clinicalView && a.translationAvailable && _translatedSummary == null)
            _card(
              child: Row(
                children: [
                  Icon(Icons.translate, color: Colors.blue),
                  SizedBox(width: 12),
                  Expanded(child: Text(AppLocalizations.of(context)!.translatedVersionAvailable,
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)))),
                  TextButton(onPressed: _translate, child: Text(AppLocalizations.of(context)!.load)),
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

          // ── Lab values table ─────────────────────────────────────────
          _sectionTitle('Lab Values'),
          if (a.structuredLabValues.isEmpty)
            _card(child: Text(AppLocalizations.of(context)!.noLabValues, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54))))
          else
            Column(
              children: a.structuredLabValues.map((lv) => _buildLabGauge(lv)).toList(),
            ),

          SizedBox(height: 24),

          // ── Abnormal findings ────────────────────────────────────────
          if (a.abnormalFindings.isNotEmpty) ...[
            _sectionTitle('Abnormal Findings'),
            ...a.abnormalFindings.map((f) {
              final name = f['test_name']?.toString() ?? '';
              final sources = a.evidenceSources
                  .where((e) => e.finding == name)
                  .expand((e) => e.sources)
                  .toSet()
                  .toList();
              return _card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: _flagColor(f['flag']?.toString() ?? 'normal').withValues(alpha: .2),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(name, style: TextStyle(
                            color: _flagColor(f['flag']?.toString() ?? 'normal'), fontWeight: FontWeight.bold)),
                      ),
                    ]),
                    if (sources.isNotEmpty) ...[
                      SizedBox(height: 8),
                      Wrap(spacing: 6, children: sources.map((s) => Chip(
                        label: Text('Based on: $s',
                            style: TextStyle(fontSize: 10, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70))),
                        backgroundColor: Theme.of(context).colorScheme.primary.withValues(alpha: 0.10),
                        padding: EdgeInsets.zero,
                      )).toList()),
                    ],
                  ],
                ),
              );
            }),
          ],
        ],
      ),
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
                label: Text(AppLocalizations.of(context)!.printPreview),
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
    padding: EdgeInsets.only(bottom: 12),
    child: Text(title, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.onSurface)),
  );

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

  Widget _buildLabGauge(LabValue lv) {
    // A simple beautiful horizontal gauge for the "Nothing" aesthetic
    final hasRange = lv.refLow != null && lv.refHigh != null;
    double progress = 0.5;
    
    if (hasRange) {
      final range = lv.refHigh! - lv.refLow!;
      if (range > 0) {
        progress = (lv.value - lv.refLow!) / range;
        // Clamp for UI rendering
        if (progress < 0) progress = 0.1;
        if (progress > 1) progress = 0.9;
      }
    }

    final color = _flagColor(lv.flag);

    return Container(
      margin: EdgeInsets.only(bottom: 12),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(lv.testName,
                    style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 15, fontWeight: FontWeight.w600)),
              ),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(lv.flag.toUpperCase(),
                    style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
              ),
            ],
          ),
          SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('${lv.value}', style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 24, fontWeight: FontWeight.bold)),
              SizedBox(width: 4),
              Padding(
                padding: EdgeInsets.only(bottom: 4),
                child: Text(lv.unit, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 12)),
              ),
              Spacer(),
              if (hasRange)
                Padding(
                  padding: EdgeInsets.only(bottom: 4),
                  child: Text('${lv.refLow} - ${lv.refHigh}', style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.38), fontSize: 12)),
                ),
            ],
          ),
          if (hasRange) ...[
            SizedBox(height: 12),
            Stack(
              children: [
                Container(
                  height: 6,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.05),
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
                Positioned(
                  left: 0,
                  child: Container(
                    height: 6,
                    width: MediaQuery.of(context).size.width * 0.8 * progress,
                    decoration: BoxDecoration(
                      color: color,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                ),
              ],
            ),
          ]
        ],
      ),
    );
  }
}