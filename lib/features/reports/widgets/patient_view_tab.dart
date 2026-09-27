import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_models.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/utils/markdown_formatter.dart';
import '../../../core/services/api_service.dart';
import '../models/report_model.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class PatientViewTab extends StatefulWidget {
  final ReportModel report;
  final ReportAnalysisModel? analysis;
  final TranslationModel? translation;
  final bool isTranslating;
  final Future<void> Function(String)? onTranslate;

  const PatientViewTab({
    super.key,
    required this.report,
    this.analysis,
    this.translation,
    this.isTranslating = false,
    this.onTranslate,
  });

  @override
  State<PatientViewTab> createState() => _PatientViewTabState();
}

class _PatientViewTabState extends State<PatientViewTab> {

  Future<void> _translate(BuildContext context) async {
    if (widget.isTranslating || widget.onTranslate == null) return;
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
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              AppLocalizations.of(context)!.translateSummary,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
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
    
    try {
      await widget.onTranslate!(selected);
    } catch (_) {
      if (mounted) {
        messenger.showSnackBar(
          SnackBar(content: Text(l10n.translationFailed)),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final report = widget.report;
    final analysis = widget.analysis;
    final theme = Theme.of(context);

    final summary = Helpers.sanitizeDisplayText(
      widget.translation?.patientSummary ??
          (analysis?.patientSummary ??
              report.aiSummary ??
              'No patient-friendly summary available for this report.'),
    );

    final rawLabs = analysis?.structuredLabValues ?? [];
    final labs = rawLabs.where((lab) => !Helpers.isMetadataParameter(lab.testName)).toList();
    final meds = analysis?.medications ?? [];
    final rawAbnormal = analysis?.abnormalFindings ?? [];
    final abnormalList = rawAbnormal.where((item) {
      final name = item['test_name']?.toString() ?? item['parameter']?.toString() ?? item['original_name']?.toString() ?? '';
      return !Helpers.isMetadataParameter(name);
    }).toList();

    final demogEntities = analysis?.entities.where((e) => 
      (e['entity_group'] == 'PatientDemographic' || e['category'] == 'PatientDemographic')
    ).toList() ?? [];

    final metadataItems = <Map<String, String>>[];
    for (var e in demogEntities) {
      final group = e['entity_group']?.toString() ?? e['category']?.toString() ?? 'Demographic';
      final word = e['word']?.toString() ?? '';
      if (word.isNotEmpty) {
        metadataItems.add({'label': group, 'value': word});
      }
    }
    for (var m in rawLabs.where((l) => Helpers.isMetadataParameter(l.testName))) {
      metadataItems.add({'label': m.testName, 'value': '${m.value} ${m.unit}'.trim()});
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Report Overview Header
          _buildOverviewCard(context, report, labs.length, meds.length, abnormalList.length),

          const SizedBox(height: 20),

          // 2. Report at a Glance Header & Translate Button
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Report at a Glance',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              widget.isTranslating
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : TextButton.icon(
                    onPressed: () => _translate(context),
                    icon: const Icon(Icons.translate, size: 16),
                    label: Text(widget.translation != null ? 'Retranslate' : 'Translate'),
                  ),
            ],
          ),
          const SizedBox(height: 10),

          // Summary Box formatted nicely without raw Markdown
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: theme.cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                MarkdownFormatter.formatText(context, summary),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Icon(Icons.auto_awesome, size: 14, color: AppColors.primary.withValues(alpha: 0.7)),
                    const SizedBox(width: 4),
                    Text(
                      analysis?.llmProvider?.toLowerCase().contains('gemini') == true || analysis?.llmProvider?.toLowerCase().contains('vertex') == true
                          ? 'Generated by Gemini AI'
                          : analysis?.llmProvider?.toLowerCase().contains('fallback') == true
                              ? 'Generated by MedNarrate Local Fallback Engine'
                              : analysis?.llmProvider?.toLowerCase().contains('ollama') == true
                                  ? 'Generated by Local Ollama AI'
                                  : 'Generated in offline mode',
                      style: TextStyle(
                        fontSize: 11,
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),

          // 3. Patient Information / Demographics (if extracted separately)
          if (metadataItems.isNotEmpty) ...[
            const Text(
              'Patient & Report Information',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: theme.cardColor,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppColors.border),
              ),
              child: Column(
                children: metadataItems.map((item) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(item['label'] ?? 'Metadata', style: const TextStyle(fontWeight: FontWeight.w600)),
                      Text(item['value'] ?? '', style: TextStyle(color: theme.colorScheme.onSurface.withValues(alpha: 0.8))),
                    ],
                  ),
                )).toList(),
              ),
            ),
            const SizedBox(height: 24),
          ],

          // 4. Important Lab Results (Cards)
          const Text(
            'Important Results',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          if (labs.isEmpty)
            _buildEmptyStateCard(context, 'No laboratory results identified in this report.')
          else
            ...labs.map((lab) => _buildLabCard(context, lab)),

          const SizedBox(height: 24),

          // 5. Reported Medications
          const Text(
            'Reported Medications',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          if (meds.isEmpty)
            _buildEmptyStateCard(context, 'No medications listed in this report.')
          else
            ...meds.map((med) => _buildMedicationCard(context, med)),

          const SizedBox(height: 24),

          // 6. What to Discuss With Your Doctor
          const Text(
            'What to Discuss With Your Doctor',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: _generateDoctorDiscussionPoints(context, abnormalList, meds, widget.translation),
            ),
          ),

          const SizedBox(height: 24),

          // 7. Medical Disclaimer
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
                    "Disclaimer: MedNarrate patient summaries provide educational context only and do not constitute a medical diagnosis or prescription. Always consult your doctor for personalized advice.",
                    style: TextStyle(
                      fontSize: 12.5,
                      height: 1.4,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
                    ),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildOverviewCard(BuildContext context, ReportModel report, int labCount, int medCount, int abnormalCount) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: AppColors.primary.withValues(alpha: 0.1),
                child: const Icon(Icons.person_outline, color: AppColors.primary, size: 26),
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
                        style: TextStyle(color: theme.colorScheme.onSurface.withValues(alpha: 0.6), fontSize: 13),
                      ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(Icons.calendar_today, size: 12, color: theme.colorScheme.primary),
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
          const SizedBox(height: 14),
          const Divider(height: 1),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildStatChip(context, '$labCount', 'Lab Results', Icons.science_outlined),
              _buildStatChip(context, '$medCount', 'Medications', Icons.medication_outlined),
              _buildStatChip(context, '$abnormalCount', 'Noteworthy', Icons.warning_amber_rounded, color: abnormalCount > 0 ? Colors.orange : null),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatChip(BuildContext context, String value, String label, IconData icon, {Color? color}) {
    final theme = Theme.of(context);
    final c = color ?? theme.colorScheme.primary;
    return Row(
      children: [
        Icon(icon, size: 16, color: c),
        const SizedBox(width: 6),
        Text(value, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: c)),
        const SizedBox(width: 4),
        Text(label, style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface.withValues(alpha: 0.6))),
      ],
    );
  }

  Widget _buildLabCard(BuildContext context, LabValue lab) {
    final theme = Theme.of(context);
    final flag = lab.flag.toLowerCase();

    Color flagColor = Colors.grey;
    String flagLabel = 'Not classified';
    if (flag == 'high') {
      flagColor = Colors.redAccent;
      flagLabel = 'High';
    } else if (flag == 'low') {
      flagColor = Colors.orange;
      flagLabel = 'Low';
    } else if (flag == 'critical') {
      flagColor = Colors.purpleAccent;
      flagLabel = 'Critical';
    } else if (flag == 'normal') {
      flagColor = const Color(0xFF00C48C);
      flagLabel = 'Normal';
    }

    String rangeText = 'Not provided in report';
    final hasRange = lab.refLow != null && lab.refHigh != null;
    if (hasRange) {
      rangeText = '${lab.refLow} – ${lab.refHigh} ${lab.unit}';
    } else if (lab.refLow != null) {
      rangeText = '> ${lab.refLow} ${lab.unit}';
    } else if (lab.refHigh != null) {
      rangeText = '< ${lab.refHigh} ${lab.unit}';
    }

    double progress = 0.5;
    if (hasRange) {
      final span = lab.refHigh! - lab.refLow!;
      if (span > 0) {
        progress = (lab.value - lab.refLow!) / span;
        if (progress < 0.05) progress = 0.05;
        if (progress > 0.95) progress = 0.95;
      }
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  lab.testName,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: flagColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  flagLabel,
                  style: TextStyle(color: flagColor, fontWeight: FontWeight.bold, fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(
                'Result: ',
                style: TextStyle(fontSize: 13, color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
              ),
              Text(
                '${lab.value} ${lab.unit}',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Reported range: $rangeText',
            style: TextStyle(fontSize: 13, color: theme.colorScheme.onSurface.withValues(alpha: 0.7)),
          ),
          const SizedBox(height: 2),
          Text(
            'Status: $flagLabel',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: flagColor),
          ),
          if (hasRange) ...[
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: progress,
                minHeight: 6,
                backgroundColor: theme.colorScheme.onSurface.withValues(alpha: 0.08),
                valueColor: AlwaysStoppedAnimation<Color>(flagColor),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMedicationCard(BuildContext context, Map<String, dynamic> med) {
    final theme = Theme.of(context);
    final name = med['medication_name']?.toString() ?? 'Medication';
    final dosage = med['dosage']?.toString() ?? 'Not specified';
    final frequency = med['frequency']?.toString() ?? 'Not specified';
    
    final times = List<String>.from(med['times_of_day'] ?? []);
    final timingText = times.isNotEmpty ? times.join(', ') : 'Not specified';
    final provenance = med['provenance']?.toString() ?? 'Report Extracted';

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.medication_outlined, color: AppColors.primary, size: 24),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 6),
                Text(
                  'Dose: $dosage',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: theme.colorScheme.onSurface.withValues(alpha: 0.9)),
                ),
                const SizedBox(height: 2),
                Text(
                  'Frequency: $frequency',
                  style: TextStyle(fontSize: 13, color: theme.colorScheme.onSurface.withValues(alpha: 0.75)),
                ),
                const SizedBox(height: 2),
                Text(
                  'Timing: $timingText',
                  style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.06),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  provenance,
                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Source: Latest report',
                style: TextStyle(fontSize: 10, color: theme.colorScheme.onSurface.withValues(alpha: 0.5)),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDoctorBullet(BuildContext context, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.check_circle_outline, size: 16, color: AppColors.primary),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 13.5, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _generateDoctorDiscussionPoints(
    BuildContext context,
    List<Map<String, dynamic>> abnormalList,
    List<Map<String, dynamic>> meds,
    TranslationModel? translation,
  ) {
    final points = <Widget>[];

    if (abnormalList.isNotEmpty) {
      for (final abnormal in abnormalList.take(3)) {
        final name = abnormal['test_name']?.toString() ?? abnormal['original_name']?.toString() ?? 'lab test';
        final val = abnormal['value']?.toString() ?? '';
        final unit = abnormal['unit']?.toString() ?? '';
        final flag = (abnormal['flag']?.toString() ?? 'abnormal').toUpperCase();

        String? translatedExpl;
        if (translation != null && translation.findingsJson.isNotEmpty) {
          try {
            final match = translation.findingsJson.firstWhere(
              (f) => f['test_name']?.toString().toLowerCase() == name.toLowerCase(),
            );
            translatedExpl = match['translated_explanation']?.toString();
          } catch (_) {}
        }

        points.add(_buildDoctorBullet(
          context,
          translatedExpl ?? 'Discuss the $flag $name level ($val $unit) with your healthcare provider.',
        ));
      }
    } else {
      points.add(_buildDoctorBullet(
        context,
        'Review your test parameters and baseline values with your doctor.',
      ));
    }

    if (meds.isNotEmpty) {
      final medNames = meds.map((m) => m['medication_name']?.toString()).where((n) => n != null).take(2).join(', ');
      if (medNames.isNotEmpty) {
        points.add(_buildDoctorBullet(
          context,
          'Confirm dosage and timing for $medNames mentioned in this report.',
        ));
      }
    } else {
      points.add(_buildDoctorBullet(
        context,
        'Confirm if any new medications or prescription changes are recommended based on these findings.',
      ));
    }

    points.add(_buildDoctorBullet(
      context,
      'Ask if follow-up testing or baseline comparisons are recommended for future monitoring.',
    ));

    return points;
  }

  Widget _buildEmptyStateCard(BuildContext context, String text) {
    final theme = Theme.of(context);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Text(
        text,
        style: TextStyle(color: theme.colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 14),
      ),
    );
  }
}
