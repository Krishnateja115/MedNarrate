import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../reports/models/report_model.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/utils/markdown_formatter.dart';
import '../../../core/services/api_service.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class SummaryTab extends StatefulWidget {
  final ReportModel report;
  final bool isProfessionalMode;

  const SummaryTab({super.key, required this.report, required this.isProfessionalMode});

  @override
  State<SummaryTab> createState() => _SummaryTabState();
}

class _SummaryTabState extends State<SummaryTab> {
  bool _translating = false;
  String? _translatedSummary;

  Future<void> _translate(BuildContext context) async {
    if (_translating) return;
    final languages = {
      'en': 'English',
      'hi': 'Hindi (हिन्दी)',
      'ta': 'Tamil (தமிழ்)',
      'te': 'Telugu (తెలుగు)',
      'kn': 'Kannada (ಕನ್ನಡ)',
      'ml': 'Malayalam (മലയാളം)',
      'mr': 'Marathi (मराठी)',
      'bn': 'Bengali (বাংলা)',
    };
    final selected = await showModalBottomSheet<String>(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(AppLocalizations.of(context)!.translateSummary, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            ...languages.entries.map((e) => ListTile(
              title: Text(e.value),
              onTap: () => Navigator.pop(context, e.key),
            )),
          ],
        ),
      ),
    );
    if (selected == null) return;
    if (!context.mounted) return;
    final messenger = ScaffoldMessenger.of(context);
    final l10n = AppLocalizations.of(context)!;
    setState(() => _translating = true);
    try {
      final t = await ApiService.instance.translateAnalysis(widget.report.id, selected);
      if (mounted) setState(() => _translatedSummary = t.patientSummary);
    } catch (_) {
      if (mounted) messenger.showSnackBar(SnackBar(content: Text(l10n.translationFailed)));
    } finally {
      if (mounted) setState(() => _translating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final report = widget.report;
    final isClinical = widget.isProfessionalMode;

    final rawSummary = Helpers.sanitizeDisplayText(
      _translatedSummary ?? (
        isClinical
          ? (report.clinicalSummary ?? 'No clinical summary available.')
          : (report.aiSummary ?? 'No patient-friendly summary available.')
      ),
    );


    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Report Overview Header Card
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: AppColors.primary.withValues(alpha: 0.1),
                  child: Icon(
                    isClinical ? Icons.medical_services_outlined : Icons.person_outline,
                    color: AppColors.primary,
                    size: 28,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        report.title,
                        style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                        overflow: TextOverflow.ellipsis,
                      ),
                      if (report.hospital.isNotEmpty && report.hospital != 'Unknown Hospital')
                        Text(
                          report.hospital,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                            fontSize: 13,
                          ),
                        ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Icon(Icons.calendar_today, size: 13, color: Theme.of(context).colorScheme.primary),
                          const SizedBox(width: 4),
                          Text(Formatters.formatDate(report.reportDate), style: const TextStyle(fontSize: 12)),
                          const SizedBox(width: 10),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.accentTeal.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              Helpers.reportTypeLabel(report.reportType),
                              style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.accentTeal),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 20),

          // View Title & Translation Action
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                isClinical ? 'Clinical Executive Summary' : 'For You — Plain Language Summary',
                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
              ),
              if (!isClinical)
                _translating
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : TextButton.icon(
                    onPressed: () => _translate(context),
                    icon: const Icon(Icons.translate, size: 16),
                    label: Text(_translatedSummary != null ? 'Retranslate' : 'Translate'),
                  ),
            ],
          ),
          const SizedBox(height: 10),

          // Formatted Summary Container (No raw markdown!)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border),
            ),
            child: MarkdownFormatter.formatText(context, rawSummary),
          ),

          const SizedBox(height: 24),
          
          // Section: Key Takeaways / Findings
          Text(
            isClinical ? 'Key Clinical Findings' : 'Important Findings',
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          
          if (report.metrics.isEmpty)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Theme.of(context).cardColor,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: Text(
                AppLocalizations.of(context)!.noKeyFindings,
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)),
              ),
            )
          else
            ...report.metrics.where((m) => m['flag'] != null && m['flag'] != 'normal' && m['flag'] != 'not_classified').map((m) {
              final flag = m['flag']?.toString() ?? 'not_classified';
              final severity = flag == 'high' || flag == 'low' ? (flag == 'high' ? 'red' : 'amber') : 'green';
              final label = '${m['parameter']} is $flag (${m['value']} ${m['unit']})';
              return _buildKeyFinding(context, label, severity, isClinical);
            }),

          const SizedBox(height: 24),

          // Medical Disclaimer Card
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.amber.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.amber.shade700.withValues(alpha: 0.3)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline_rounded, color: Colors.amber.shade800, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    "Disclaimer: MedNarrate AI summary is for informational purposes only and does not replace medical advice. Always consult a qualified physician for clinical decisions.",
                    style: TextStyle(
                      fontSize: 12.5,
                      height: 1.4,
                      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.8),
                    ),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildKeyFinding(BuildContext context, String text, String severity, bool isClinical) {
    Color dotColor = Colors.green;
    if (severity == 'amber') dotColor = Colors.orange;
    if (severity == 'red') dotColor = Colors.red;

    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        leading: Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(shape: BoxShape.circle, color: dotColor),
        ),
        title: Text(text, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            margin: const EdgeInsets.only(bottom: 12, left: 24, right: 8),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.border),
            ),
            child: Text(
              isClinical
                ? "Clinical Finding Note: Out-of-range measurement observed. Review patient history and cross-reference with baseline laboratory parameters."
                : "What does this mean? This result is outside the standard reference range. Please discuss this finding with your physician during your next consultation.",
              style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.75), fontSize: 13, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}
