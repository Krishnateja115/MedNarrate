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
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text('AI Analysis'),
        actions: [
          if (_status == 'completed')
            IconButton(
              onPressed: () => context.push(Routes.aiChat, extra: widget.reportId),
              icon: const Icon(Icons.chat_bubble_outline),
              tooltip: 'Ask AI about this report',
            ),
        ],
      ),
      body: switch (_status) {
        'loading' => const Padding(padding: EdgeInsets.all(20), child: SkeletonAnalysis()),
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
          const SizedBox(height: 28),
          const Text('Analyzing your report…',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: Colors.white)),
          const SizedBox(height: 10),
          const Text('AI is reading your document. This may take a minute.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white54, fontSize: 13)),
          const SizedBox(height: 32),
          _processingStep('Reading document text', true),
          _processingStep('Extracting medical data', true),
          _processingStep('Running AI analysis', false),
        ],
      ),
    );
  }

  Widget _processingStep(String label, bool done) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(done ? Icons.check_circle : Icons.radio_button_unchecked,
            color: done ? const Color(0xFF00C48C) : Colors.white24, size: 18),
        const SizedBox(width: 10),
        Text(label, style: TextStyle(color: done ? Colors.white70 : Colors.white30, fontSize: 13)),
      ]),
    );
  }

  Widget _buildFailed() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 60),
            const SizedBox(height: 16),
            const Text('Analysis Failed', style: TextStyle(fontSize: 22, color: Colors.white, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Text(_errorReason ?? 'An unknown error occurred.',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white70)),
            const SizedBox(height: 28),
            FilledButton.icon(
              onPressed: _retry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry Analysis'),
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
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 90),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Dual-mode toggle ──────────────────────────────────────────
          Container(
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Row(
              children: [
                Expanded(child: _modeTab('For You', !_clinicalView, () => setState(() => _clinicalView = false))),
                Expanded(child: _modeTab('Clinical View', _clinicalView, () => setState(() => _clinicalView = true))),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── Summary card with TTS ─────────────────────────────────────
          Row(
            children: [
              const Expanded(child: Text('Summary',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white))),
              ValueListenableBuilder<TtsState>(
                valueListenable: _tts.stateNotifier,
                builder: (_, ttsState, __) => IconButton(
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
          const SizedBox(height: 8),
          _card(
            child: Text(activeSummary.isEmpty ? 'No summary available.' : activeSummary,
                style: const TextStyle(color: Colors.white70, height: 1.6)),
          ),
          const SizedBox(height: 12),

          // Translate button
          if (!_clinicalView && a.translationAvailable && _translatedSummary == null)
            _card(
              child: Row(
                children: [
                  const Icon(Icons.translate, color: Colors.blue),
                  const SizedBox(width: 12),
                  Expanded(child: Text('Translated version available',
                      style: const TextStyle(color: Colors.white70))),
                  TextButton(onPressed: _translate, child: const Text('Load')),
                ],
              ),
            ),
          if (!_clinicalView && !a.translationAvailable && _translatedSummary == null)
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                onPressed: _translating ? null : _translate,
                icon: _translating
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.translate),
                label: Text(_translating ? 'Translating…' : 'Translate to preferred language'),
              ),
            ),

          const SizedBox(height: 24),

          // ── Lab values table ─────────────────────────────────────────
          _sectionTitle('Lab Values'),
          if (a.structuredLabValues.isEmpty)
            _card(child: const Text('No lab values found.', style: TextStyle(color: Colors.white54)))
          else
            _card(
              child: Table(
                columnWidths: const {
                  0: FlexColumnWidth(3),
                  1: FlexColumnWidth(2),
                  2: FlexColumnWidth(2),
                  3: FlexColumnWidth(1.5),
                },
                children: [
                  TableRow(
                    decoration: BoxDecoration(
                      border: Border(bottom: BorderSide(color: Colors.white12))),
                    children: ['Test', 'Value', 'Range', 'Flag']
                        .map((h) => Padding(
                              padding: const EdgeInsets.only(bottom: 8),
                              child: Text(h,
                                  style: const TextStyle(
                                      color: Colors.white54, fontWeight: FontWeight.w600, fontSize: 12)),
                            ))
                        .toList(),
                  ),
                  ...a.structuredLabValues.map((lv) => TableRow(
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6),
                        child: Text(lv.testName,
                            style: const TextStyle(color: Colors.white, fontSize: 13))),
                      Text('${lv.value} ${lv.unit}',
                          style: const TextStyle(color: Colors.white70, fontSize: 13)),
                      Text(lv.refLow != null && lv.refHigh != null
                          ? '${lv.refLow}–${lv.refHigh}'
                          : '—',
                          style: const TextStyle(color: Colors.white54, fontSize: 12)),
                      Container(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: _flagColor(lv.flag).withValues(alpha: .2),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(lv.flag.toUpperCase(),
                            style: TextStyle(
                                color: _flagColor(lv.flag), fontSize: 10, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  )),
                ],
              ),
            ),

          const SizedBox(height: 24),

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
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: _flagColor(f['flag']?.toString() ?? 'normal').withValues(alpha: .2),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(name, style: TextStyle(
                            color: _flagColor(f['flag']?.toString() ?? 'normal'), fontWeight: FontWeight.bold)),
                      ),
                    ]),
                    if (sources.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Wrap(spacing: 6, children: sources.map((s) => Chip(
                        label: Text('Based on: $s',
                            style: const TextStyle(fontSize: 10, color: Colors.white70)),
                        backgroundColor: Colors.white10,
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
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
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
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.picture_as_pdf_outlined),
                label: Text(_exporting ? 'Exporting…' : 'Export PDF'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  side: const BorderSide(color: AppColors.primary),
                  foregroundColor: AppColors.primary,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: FilledButton.icon(
                onPressed: () => ExportService.instance.printSummary(
                  analysis: a,
                  reportTitle: 'Report Analysis',
                  reportDate: a.processedAt?.toLocal().toString().split(' ').first ?? '',
                ),
                icon: const Icon(Icons.print_outlined),
                label: const Text('Print / Preview'),
                style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
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
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.all(4),
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: active ? AppColors.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(label,
            textAlign: TextAlign.center,
            style: TextStyle(
                color: active ? Colors.white : Colors.white54,
                fontWeight: active ? FontWeight.bold : FontWeight.normal)),
      ),
    );
  }

  Widget _sectionTitle(String title) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
  );

  Widget _card({required Widget child}) => Container(
    width: double.infinity,
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(14),
    ),
    child: child,
  );
}