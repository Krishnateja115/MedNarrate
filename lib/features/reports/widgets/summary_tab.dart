import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../reports/models/report_model.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/utils/helpers.dart';
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
    // Show language picker
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
            Text(AppLocalizations.of(context)!.translateSummary, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
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
    setState(() => _translating = true);
    try {
      final t = await ApiService.instance.translateAnalysis(widget.report.id, selected);
      if (mounted) setState(() => _translatedSummary = t.patientSummary);
    } catch (_) {
      if (mounted) messenger.showSnackBar(SnackBar(content: Text(AppLocalizations.of(context)!.translationFailed)));
    } finally {
      if (mounted) setState(() => _translating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final report = widget.report;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Report Info Card
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
                  radius: 30,
                  backgroundColor: AppColors.primary.withValues(alpha: 0.1),
                  child: Icon(Icons.description, color: AppColors.primary, size: 30),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(report.title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold), overflow: TextOverflow.ellipsis),
                      if (report.hospital.isNotEmpty && report.hospital != 'Unknown Hospital')
                        Text(report.hospital, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5))),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Icon(Icons.calendar_today, size: 14, color: Theme.of(context).colorScheme.primary),
                          const SizedBox(width: 4),
                          Text(Formatters.formatDate(report.reportDate), style: const TextStyle(fontSize: 12)),
                          const SizedBox(width: 12),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.accentTeal.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(Helpers.reportTypeLabel(report.reportType), style: const TextStyle(fontSize: 10, color: AppColors.accentTeal)),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          
          SizedBox(height: 24),

          // Abnormal Values Alert
          if (report.metrics.any((m) => m['flag'] != null && m['flag'] != 'normal'))
            Container(
              margin: const EdgeInsets.only(bottom: 24),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.red.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(12),
                border: const Border(left: BorderSide(color: Colors.red, width: 4)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: Colors.red),
                      const SizedBox(width: 8),
                      Text(AppLocalizations.of(context)!.abnormalValuesDetected, style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(AppLocalizations.of(context)!.someParametersOutOfRange, style: const TextStyle(fontSize: 13)),
                  const SizedBox(height: 8),
                  Text(AppLocalizations.of(context)!.consultYourDoctor, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                ],
              ),
            ),
            
          // Summary Section
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                widget.isProfessionalMode ? 'Clinical Summary' : 'Patient-Friendly Summary',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              if (!widget.isProfessionalMode)
                _translating
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : TextButton.icon(
                    onPressed: () => _translate(context),
                    icon: const Icon(Icons.translate, size: 16),
                    label: Text(_translatedSummary != null ? 'Retranslate' : 'Translate'),
                  ),
            ],
          ),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border),
            ),
            child: SelectableText(
              _translatedSummary ?? (
                widget.isProfessionalMode 
                  ? (report.clinicalSummary ?? 'No clinical summary available.')
                  : (report.aiSummary ?? 'No patient-friendly summary available.')
              ),
              style: const TextStyle(height: 1.6, fontSize: 15),
            ),
          ),

          const SizedBox(height: 24),
          
          Text(AppLocalizations.of(context)!.keyFindings, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          
          if (report.metrics.isEmpty)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Theme.of(context).cardColor,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: Text(AppLocalizations.of(context)!.noKeyFindings,
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54))),
            )
          else
            ...report.metrics.where((m) => m['flag'] != null && m['flag'] != 'normal').map((m) {
              final flag = m['flag']?.toString() ?? 'normal';
              final severity = flag == 'high' || flag == 'low' ? (flag == 'high' ? 'red' : 'amber') : 'green';
              final label = '${m['parameter']} is $flag (${m['value']} ${m['unit']})';
              return _buildKeyFinding(context, label, severity);
            }),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildKeyFinding(BuildContext context, String text, String severity) {
    Color dotColor = Colors.green;
    if (severity == 'amber') dotColor = Colors.orange;
    if (severity == 'red') dotColor = Colors.red;

    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        leading: Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(shape: BoxShape.circle, color: dotColor),
        ),
        title: Text(text, style: TextStyle(fontWeight: FontWeight.w500)),
        children: [
          Container(
            padding: EdgeInsets.all(12),
            margin: EdgeInsets.only(bottom: 12, left: 32, right: 16),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.border),
            ),
            child: Text(
              "What does this mean? This finding suggests a need for lifestyle changes or medical review. Please discuss this with your physician.",
              style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7), fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}
