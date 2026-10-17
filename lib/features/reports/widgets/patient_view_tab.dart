import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/l10n/app_l10n.dart';
import '../../../core/l10n/locale_notifier.dart';
import '../../../core/l10n/report_ui_labels.dart';
import '../../../core/services/api_models.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/utils/markdown_formatter.dart';
import '../../../core/utils/report_text_structurer.dart';
import '../models/report_model.dart';
import 'package:mednarrate/l10n/app_localizations.dart';
import '../../../core/services/api_exception.dart';
import 'translation_parameter_name.dart';
import 'lab_flag_sheet.dart';

class PatientViewTab extends StatefulWidget {
  final ReportModel report;
  final ReportAnalysisModel? analysis;
  final TranslationModel? translation;
  final bool isTranslating;
  final Future<void> Function(String)? onTranslate;

  /// Language currently being fetched, if any (for the selector UI only).
  final String? pendingLanguage;

  const PatientViewTab({
    super.key,
    required this.report,
    this.analysis,
    this.translation,
    this.isTranslating = false,
    this.onTranslate,
    this.pendingLanguage,
  });

  @override
  State<PatientViewTab> createState() => _PatientViewTabState();
}

class _PatientViewTabState extends State<PatientViewTab> {
  String _label(String key, {required String fallback}) {
    final t = widget.translation;
    // Labels of the active report translation, else the app-language word list
    // (empty for English, which then uses [fallback]).
    final labels = effectiveReportUiLabels(t);
    final bool isTranslated = t != null && t.language != 'en';

    if (labels.isEmpty) {
      return isTranslated ? '' : fallback;
    }
    final val = labels[key];
    if (val != null && val.trim().isNotEmpty) {
      return val.trim();
    }
    if (isTranslated) {
      return '';
    }
    return fallback;
  }

  static const Map<String, String> _languages = {
    'en': 'English',
    'hi': 'Hindi (हिन्दी)',
    'ta': 'Tamil (தமிழ்)',
    'te': 'Telugu (తెలుగు)',
    'kn': 'Kannada (ಕನ್ನಡ)',
    'ml': 'Malayalam (മലയാളം)',
    'mr': 'Marathi (मराठी)',
    'bn': 'Bengali (বাংলা)',
  };

  /// Native display name for the selector button, e.g. "हिन्दी".
  static String _nativeName(String code) {
    final full = _languages[code] ?? code;
    final m = RegExp(r'\((.+)\)').firstMatch(full);
    return m?.group(1) ?? full;
  }

  Future<void> _translate(BuildContext context) async {
    // The selector stays usable while a request is in flight; the controller
    // supersedes stale requests, so the user is never locked out.
    if (widget.onTranslate == null) return;
    final languages = _languages;
    final current =
        widget.pendingLanguage ?? widget.translation?.language ?? 'en';
    final selected = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (sheetCtx) {
        return DraggableScrollableSheet(
          initialChildSize: 0.5,
          minChildSize: 0.3,
          maxChildSize: 0.85,
          expand: false,
          builder: (_, scrollController) => Column(
            children: [
              const SizedBox(height: 12),
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[400],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                AppLocalizations.of(context)!.translateSummary,
                style:
                    const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Expanded(
                child: ListView(
                  controller: scrollController,
                  children: [
                    ...languages.entries.map((e) => ListTile(
                          key: ValueKey('lang_option_${e.key}'),
                          title: Text(e.value),
                          selected: e.key == current,
                          trailing: e.key == current
                              ? const Icon(Icons.check_rounded)
                              : null,
                          onTap: () => Navigator.pop(sheetCtx, e.key),
                        )),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
    if (selected == null) return;
    if (!context.mounted) return;

    final messenger = ScaffoldMessenger.of(context);
    final l10n = AppLocalizations.of(context)!;

    try {
      await widget.onTranslate!(selected);
    } catch (e) {
      if (mounted) {
        final errorMsg =
            (e is ApiException) ? e.message : l10n.translationFailed;
        messenger.showSnackBar(
          SnackBar(content: Text(errorMsg)),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final report = widget.report;
    final analysis = widget.analysis;
    final theme = Theme.of(context);
    final t = widget.translation;

    // Translated summaries that were stored without line breaks are given
    // their section structure back for display only (stored text untouched).
    final summary = Helpers.sanitizeDisplayText(
      t != null
          ? ReportTextStructurer.restoreStructure(t.patientSummary)
          : (analysis?.patientSummary ??
              report.aiSummary ??
              AppLocalizations.of(context)!.noPatientSummary),
    );

    final rawLabs = analysis?.structuredLabValues ?? [];
    final labs = rawLabs
        .where((lab) => !Helpers.isMetadataParameter(lab.testName))
        .toList();
    final meds = analysis?.medications ?? [];
    final rawAbnormal = analysis?.abnormalFindings ?? [];
    final abnormalList = rawAbnormal.where((item) {
      final name = item['test_name']?.toString() ??
          item['parameter']?.toString() ??
          item['original_name']?.toString() ??
          '';
      return !Helpers.isMetadataParameter(name);
    }).toList();

    final demogEntities = analysis?.entities
            .where((e) => (e['entity_group'] == 'PatientDemographic' ||
                e['category'] == 'PatientDemographic'))
            .toList() ??
        [];

    final metadataItems = <Map<String, String>>[];
    for (var e in demogEntities) {
      final group = e['entity_group']?.toString() ??
          e['category']?.toString() ??
          'Demographic';
      final word = e['word']?.toString() ?? '';
      if (word.isNotEmpty) {
        metadataItems.add({'label': group, 'value': word});
      }
    }
    for (var m
        in rawLabs.where((l) => Helpers.isMetadataParameter(l.testName))) {
      metadataItems.add({
        'label': m.testName,
        'value': '${m.value} ${m.unit}'.trim(),
      });
    }

    // AI attribution line (translated when translation exists for the active provider).
    final llmProv = analysis?.llmProvider?.toLowerCase() ?? '';
    final String aiAttribution;
    if (llmProv.contains('gemini') || llmProv.contains('vertex')) {
      aiAttribution = _label('label_generated_by_gemini',
          fallback: 'Generated by Gemini AI');
    } else if (llmProv.contains('fallback')) {
      aiAttribution = _label('label_generated_by_local_fallback',
          fallback: 'Generated by MedNarrate Local Fallback Engine');
    } else if (llmProv.contains('ollama')) {
      aiAttribution = _label('label_generated_by_ollama',
          fallback: 'Generated by Local Ollama AI');
    } else {
      aiAttribution = _label('label_generated_offline',
          fallback: 'Generated in offline mode');
    }

    // Selector button label: always show the active (or loading) language so
    // the button never renders empty when a ui label key is missing.
    final selectorLanguage =
        widget.pendingLanguage ?? widget.translation?.language ?? 'en';
    final translateBtn = selectorLanguage == 'en'
        ? _label('label_translate', fallback: 'Translate')
        : _nativeName(selectorLanguage);

    final disclaimerPatient = _label('label_disclaimer_patient',
        fallback:
            'Disclaimer: MedNarrate patient summaries provide educational context only and do not constitute a medical diagnosis or prescription. Always consult your doctor for personalized advice.');

    final sectionPatientReportInfo = _label('section_patient_report_info',
        fallback: 'Patient & Report Information');

    final sourceLatestReport =
        _label('label_source_latest_report', fallback: 'Source: Latest report');

    final labelReportExtracted =
        _label('label_report_extracted', fallback: 'Report Extracted');

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Report Overview Header
          _buildOverviewCard(context, report, labs.length, meds.length,
              abnormalList.length, t),

          const SizedBox(height: 20),

          // 2. Report at a Glance Header & Translate Button
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  _label('section_report_at_a_glance',
                      fallback: 'Report at a Glance'),
                  style:
                      const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),
              TextButton.icon(
                key: const ValueKey('language_selector_button'),
                onPressed: () => _translate(context),
                icon: widget.isTranslating
                    ? const SizedBox(
                        width: 14,
                        height: 14,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.translate, size: 16),
                label: Text(translateBtn.isEmpty ? 'Translate' : translateBtn),
              ),
            ],
          ),
          const SizedBox(height: 10),
          if (widget.isTranslating)
            Container(
              key: const ValueKey('translating_banner'),
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: theme.colorScheme.primary.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      AppLocalizations.of(context)!.translatingReportBanner,
                      style: TextStyle(
                        fontSize: 13,
                        color: theme.colorScheme.onSurface
                            .withValues(alpha: 0.75),
                      ),
                    ),
                  ),
                ],
              ),
            ),

          // Summary Box formatted nicely without raw Markdown
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: theme.cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                  color: Theme.of(context).colorScheme.outlineVariant),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                MarkdownFormatter.formatText(context, summary),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Icon(Icons.auto_awesome,
                        size: 14,
                        color: Theme.of(context)
                            .colorScheme
                            .primary
                            .withValues(alpha: 0.7)),
                    const SizedBox(width: 4),
                    Flexible(
                      child: Text(
                        aiAttribution,
                        textAlign: TextAlign.end,
                        style: TextStyle(
                          fontSize: 11,
                          color:
                              theme.colorScheme.onSurface.withValues(alpha: 0.5),
                          fontStyle: FontStyle.italic,
                        ),
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
            Text(
              sectionPatientReportInfo,
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: theme.cardColor,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                    color: Theme.of(context).colorScheme.outlineVariant),
              ),
              child: Column(
                children: metadataItems
                    .map((item) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Flexible(
                                child: Text(item['label'] ?? AppLocalizations.of(context)!.metadataFallback,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w600)),
                              ),
                              const SizedBox(width: 12),
                              Flexible(
                                child: Text(item['value'] ?? '',
                                    textAlign: TextAlign.end,
                                    style: TextStyle(
                                        color: theme.colorScheme.onSurface
                                            .withValues(alpha: 0.8))),
                              ),
                            ],
                          ),
                        ))
                    .toList(),
              ),
            ),
            const SizedBox(height: 24),
          ],

          // 4. Important Lab Results (Cards)
          Text(
            _label('section_important_results', fallback: 'Important Results'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          if (labs.isEmpty)
            _buildEmptyStateCard(
                context,
                _label('label_no_lab_results',
                    fallback:
                        'No laboratory results identified in this report.'))
          else
            ...labs.map((lab) => _buildLabCard(context, lab, t)),

          const SizedBox(height: 24),

          // 5. Reported Medications
          Text(
            _label('section_reported_medications',
                fallback: 'Reported Medications'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          if (meds.isEmpty)
            _buildEmptyStateCard(
                context,
                _label('label_no_medications',
                    fallback: 'No medications listed in this report.'))
          else
            ...meds.map((med) => _buildMedicationCard(
                  context,
                  med,
                  translation: t,
                  labelReportExtracted: labelReportExtracted,
                  sourceLatestReport: sourceLatestReport,
                )),

          const SizedBox(height: 24),

          // 6. What to Discuss With Your Doctor
          Text(
            _label('section_what_to_discuss',
                fallback: 'What to Discuss With Your Doctor'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                  color: Theme.of(context).colorScheme.outlineVariant),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: _buildDoctorDiscussionPoints(
                context,
                abnormalList,
                meds,
                t,
              ),
            ),
          ),

          const SizedBox(height: 24),

          // 7. Medical Disclaimer
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.amber.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                  color: Colors.amber.shade700.withValues(alpha: 0.3)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline_rounded,
                    color: Colors.amber.shade800, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    disclaimerPatient,
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

  Widget _buildOverviewCard(BuildContext context, ReportModel report,
      int labCount, int medCount, int abnormalCount,
      [TranslationModel? translation]) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: Theme.of(context)
                    .colorScheme
                    .primary
                    .withValues(alpha: 0.1),
                child: Icon(
                  Icons.person_outline,
                  color: AppColors.primary,
                  size: 26,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      report.title,
                      style: const TextStyle(
                          fontSize: 17, fontWeight: FontWeight.bold),
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (report.hospital.isNotEmpty &&
                        report.hospital != 'Unknown Hospital')
                      Text(
                        report.hospital,
                        style: TextStyle(
                            color: theme.colorScheme.onSurface
                                .withValues(alpha: 0.6),
                            fontSize: 13),
                      ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(Icons.calendar_today,
                            size: 12, color: theme.colorScheme.primary),
                        const SizedBox(width: 4),
                        Text(
                            Formatters.formatDate(report.reportDate,
                                translation?.language),
                            style: const TextStyle(fontSize: 12)),
                        const SizedBox(width: 10),
                        Flexible(
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.accentTeal.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              Helpers.reportTypeLabelIn(
                                  report.reportType,
                                  translation != null &&
                                          translation.language != 'en'
                                      ? translation.language
                                      : appLanguageCode),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.accentTeal),
                            ),
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
          IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(
                  child: _buildStatChip(
                      context,
                      '$labCount',
                      _label('chip_lab_results', fallback: 'Lab Results'),
                      Icons.science_outlined),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildStatChip(
                      context,
                      '$medCount',
                      _label('chip_medications', fallback: 'Medications'),
                      Icons.medication_outlined),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildStatChip(
                      context,
                      '$abnormalCount',
                      _label('chip_noteworthy', fallback: 'Noteworthy'),
                      Icons.warning_amber_rounded,
                      color: abnormalCount > 0 ? Colors.orange : null),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatChip(
      BuildContext context, String value, String label, IconData icon,
      {Color? color}) {
    final theme = Theme.of(context);
    final c = color ?? theme.colorScheme.primary;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
      decoration: BoxDecoration(
        color: c.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 16, color: c),
              const SizedBox(width: 6),
              Text(value,
                  style: TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 18, color: c)),
            ],
          ),
          const SizedBox(height: 4),
          Text(label,
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                  fontSize: 12,
                  height: 1.25,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.65))),
        ],
      ),
    );
  }

  Widget _buildLabCard(BuildContext context, LabValue lab,
      [TranslationModel? translation]) {
    final theme = Theme.of(context);
    final flag = lab.flag.toLowerCase();
    final l = effectiveReportUiLabels(translation);
    final isProvisional = lab.referenceSource == 'general_provisional';

    Color flagColor = Colors.grey;
    String flagLabel = l['label_not_classified'] ?? 'No reference range';
    if (flag == 'high') {
      flagColor = Colors.redAccent;
      flagLabel = l['label_high'] ?? 'High';
    } else if (flag == 'low') {
      flagColor = Colors.orange;
      flagLabel = l['label_low'] ?? 'Low';
    } else if (flag == 'critical') {
      flagColor = AppColors.warning;
      flagLabel = l['label_critical'] ?? 'Critical';
    } else if (flag == 'normal') {
      flagColor = const Color(0xFF00C48C);
      flagLabel = l['label_normal'] ?? 'Normal';
    }

    String rangeText = l['label_not_provided'] ?? 'Not provided in report';
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
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  translatedParameterName(lab.testName, widget.translation),
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.bold),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: flagColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  isProvisional
                      ? '$flagLabel · ${AppLocalizations.of(context)!.provisionalWord}'
                      : flagLabel,
                  style: TextStyle(
                      color: flagColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(
                '${l['label_result'] ?? 'Result'}: ',
                style: TextStyle(
                    fontSize: 13,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
              ),
              Flexible(
                child: Text(
                  '${lab.value} ${lab.unit}',
                  style:
                      const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '${isProvisional ? AppLocalizations.of(context)!.generalComparisonRange : (l['label_reported_range'] ?? 'Reported range')}: $rangeText',
            style: TextStyle(
                fontSize: 13,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.7)),
          ),
          const SizedBox(height: 2),
          Text(
            '${l['label_status'] ?? 'Status'}: $flagLabel${isProvisional ? ' (${AppLocalizations.of(context)!.provisionalWord})' : ''}',
            style: TextStyle(
                fontSize: 12, fontWeight: FontWeight.w600, color: flagColor),
          ),
          if (isProvisional) ...[
            const SizedBox(height: 6),
            Text(
              AppLocalizations.of(context)!.provisionalNote(lab.referenceSourceUrl ?? 'MedlinePlus'),
              style: TextStyle(
                  fontSize: 11,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.65)),
            ),
          ],
          if (hasRange) ...[
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: progress,
                minHeight: 6,
                backgroundColor:
                    theme.colorScheme.onSurface.withValues(alpha: 0.08),
                valueColor: AlwaysStoppedAnimation<Color>(flagColor),
              ),
            ),
          ],
          Align(
            alignment: AlignmentDirectional.centerEnd,
            child: TextButton.icon(
              onPressed: () => showLabFlagSheet(
                context,
                testName: translatedParameterName(lab.testName, widget.translation),
                value: lab.value,
                unit: lab.unit,
                refLow: lab.refLow,
                refHigh: lab.refHigh,
                flag: flag,
                isProvisional: isProvisional,
              ),
              icon: const Icon(Icons.help_outline, size: 16),
              label: Text(AppLocalizations.of(context)!.mlWhyFlagged,
                  style: const TextStyle(fontSize: 12.5)),
              style: TextButton.styleFrom(
                visualDensity: VisualDensity.compact,
                padding: const EdgeInsets.symmetric(horizontal: 6),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMedicationCard(
    BuildContext context,
    Map<String, dynamic> med, {
    TranslationModel? translation,
    required String labelReportExtracted,
    required String sourceLatestReport,
  }) {
    final theme = Theme.of(context);
    String name = med['medication_name']?.toString() ?? 'Medication';
    final l = effectiveReportUiLabels(translation);
    String dosage =
        med['dosage']?.toString() ?? l['label_unspecified'] ?? 'Not specified';
    String frequency = med['frequency']?.toString() ??
        l['label_unspecified'] ??
        'Not specified';

    List<String> times = List<String>.from(med['times_of_day'] ?? []);
    String instructions = med['instructions']?.toString() ?? '';

    if (translation != null && translation.medicationsJson.isNotEmpty) {
      try {
        final match = translation.medicationsJson.firstWhere(
          (m) =>
              m['medication_name']?.toString().toLowerCase() ==
              name.toLowerCase(),
        );
        name = match['translated_medication_name']?.toString() ?? name;
        dosage = match['translated_dosage']?.toString() ?? dosage;
        frequency = match['translated_frequency']?.toString() ?? frequency;
        final tTimes = match['translated_times_of_day'];
        if (tTimes is List) {
          times = List<String>.from(tTimes);
        } else if (tTimes is String && tTimes.isNotEmpty) {
          times = [tTimes];
        }
        final tInst = match['translated_instructions']?.toString();
        if (tInst != null && tInst.trim().isNotEmpty) {
          instructions = tInst;
        }
      } catch (_) {}
    }

    final timingText = times.isNotEmpty
        ? times.join(', ')
        : (l['label_not_provided'] ?? 'Not specified');
    final provenance = med['provenance']?.toString() ?? labelReportExtracted;

    final List<Widget> medInfo = [
      Text(name,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
      const SizedBox(height: 6),
      Text('${l['label_dose'] ?? 'Dose'}: $dosage',
          style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.9))),
      const SizedBox(height: 2),
      Text('${l['label_frequency'] ?? 'Frequency'}: $frequency',
          style: TextStyle(
              fontSize: 13,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.75))),
      const SizedBox(height: 2),
      Text('${l['label_timing'] ?? 'Timing'}: $timingText',
          style: TextStyle(
              fontSize: 12,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6))),
    ];
    if (instructions.trim().isNotEmpty) {
      medInfo.addAll([
        const SizedBox(height: 6),
        Text(
          instructions.trim(),
          style: TextStyle(
              fontSize: 12,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
              fontStyle: FontStyle.italic),
        ),
      ]);
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.medication_outlined,
                color: AppColors.primary, size: 24),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: medInfo),
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
                  style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color:
                          theme.colorScheme.onSurface.withValues(alpha: 0.6)),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                sourceLatestReport,
                style: TextStyle(
                    fontSize: 10,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.5)),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDoctorBullet(BuildContext context, String text) {
    if (text.trim().isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.check_circle_outline,
              size: 16, color: AppColors.primary),
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

  /// "Discuss this result" bullet. In a non-English app language the bundled
  /// template (same one the server uses) is filled in; English keeps the
  /// original sentence.
  String _discussBullet(String flag, String name, String val, String unit) {
    final labels = bundledReportUiLabels(localeModeNotifier.value.languageCode);
    final template = labels['dp_abnormal'];
    if (template == null) {
      return 'Discuss the $flag $name level ($val $unit) with your healthcare provider.';
    }
    final flagText = labels['label_${flag.toLowerCase()}'] ?? flag;
    return template
        .replaceAll('{test}', name)
        .replaceAll('{flag}', flagText)
        .replaceAll('{value}', val)
        .replaceAll('{unit}', unit)
        .replaceAll(RegExp(r'\(\s+'), '(')
        .replaceAll(RegExp(r'\s+\)'), ')')
        .replaceAll(RegExp(r'\(\s*\)'), '')
        .replaceAll(RegExp(r'[ \t]{2,}'), ' ')
        .trim();
  }

  List<Widget> _buildDoctorDiscussionPoints(
    BuildContext context,
    List<Map<String, dynamic>> abnormalList,
    List<Map<String, dynamic>> meds,
    TranslationModel? translation,
  ) {
    final points = <Widget>[];
    final isTranslated = translation != null && translation.language != 'en';

    // ------------------------------------------------------------------
    // PRIMARY SOURCE: backend-generated structured doctor_discussion_points.
    // These are fully translated per-language sentences already constructed
    // by the LLM — including flag/test/value/unit when appropriate.
    // Flutter MUST NOT construct English templates here.
    // ------------------------------------------------------------------
    final backendDiscussion = translation?.doctorDiscussionPoints ?? [];

    if (isTranslated && backendDiscussion.isNotEmpty) {
      for (final s in backendDiscussion) {
        final txt = s.trim();
        if (txt.isEmpty) continue;
        points.add(_buildDoctorBullet(context, txt));
      }
      // Guard: if backend somehow returned fewer points than we expect, still
      // do NOT fall back to English templates. If the backend discussion
      // points were short, we silently use what was provided.
      // (The backend validation should already guarantee completeness before
      // caching the response, so in practice this guard is rarely hit.)
      return points;
    }

    // ------------------------------------------------------------------
    // FALLBACK PATH (English mode or old translation records without
    // doctor_discussion_points populated). Here we synthesize bullets but
    // only in ENGLISH — because the code below intentionally matches the
    // historic English-only behavior. For any non-English request, the
    // backend validation should already have refused to cache/return a
    // record with empty doctor_discussion_points, so this branch is not
    // reachable for translated reports.
    // ------------------------------------------------------------------
    if (abnormalList.isNotEmpty) {
      for (final abnormal in abnormalList.take(3)) {
        final name = abnormal['test_name']?.toString() ??
            abnormal['original_name']?.toString() ??
            'lab test';
        final val = abnormal['value']?.toString() ?? '';
        final unit = abnormal['unit']?.toString() ?? '';
        final flag = (abnormal['flag']?.toString() ?? 'abnormal').toUpperCase();

        String? translatedExpl;
        if (translation != null && translation.findingsJson.isNotEmpty) {
          try {
            final match = translation.findingsJson.firstWhere(
              (f) =>
                  f['test_name']?.toString().toLowerCase() ==
                  name.toLowerCase(),
            );
            translatedExpl = match['translated_explanation']?.toString();
          } catch (_) {}
        }

        final String bullet;
        if (translatedExpl != null && translatedExpl.trim().isNotEmpty) {
          bullet = translatedExpl.trim();
        } else if (!isTranslated) {
          // Only English uses the Flutter template.
          bullet = _discussBullet(flag, name, val, unit);
        } else {
          // Safety net: translated mode + no backend discussion + no
          // translated explanation = surface a translated generic
          // "discuss with your doctor" label so no English leaks.
          final generic = effectiveReportUiLabels(translation)['label_review_test_parameters'];
          bullet = (generic != null && generic.trim().isNotEmpty)
              ? generic.trim()
              : (isTranslated
                  ? ''
                  : 'Review your test parameters and baseline values with your doctor.');
        }
        points.add(_buildDoctorBullet(context, bullet));
      }
    } else {
      final generic = effectiveReportUiLabels(translation)['label_review_test_parameters'];
      final text = (generic != null && generic.trim().isNotEmpty)
          ? generic.trim()
          : (isTranslated
              ? ''
              : 'Review your test parameters and baseline values with your doctor.');
      points.add(_buildDoctorBullet(context, text));
    }

    if (meds.isNotEmpty) {
      final medNames = meds
          .map((m) => m['medication_name']?.toString())
          .where((n) => n != null)
          .take(2)
          .join(', ');
      if (medNames.isNotEmpty) {
        final label = effectiveReportUiLabels(translation)['label_confirm_dosage_timing'];
        final text = (label != null && label.trim().isNotEmpty)
            ? label.trim()
            : (isTranslated
                ? ''
                : 'Confirm dosage and timing for the medications mentioned in this report.');
        points.add(_buildDoctorBullet(context, text));
      }
    } else {
      final label = effectiveReportUiLabels(translation)['label_confirm_new_medications'];
      final text = (label != null && label.trim().isNotEmpty)
          ? label.trim()
          : (isTranslated
              ? ''
              : 'Confirm if any new medications or prescription changes are recommended based on these findings.');
      points.add(_buildDoctorBullet(context, text));
    }

    {
      final label = effectiveReportUiLabels(translation)['label_confirm_followup'];
      final text = (label != null && label.trim().isNotEmpty)
          ? label.trim()
          : (isTranslated
              ? ''
              : 'Ask if follow-up testing or baseline comparisons are recommended for future monitoring.');
      points.add(_buildDoctorBullet(context, text));
    }

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
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Text(
        text,
        style: TextStyle(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.54),
            fontSize: 14),
      ),
    );
  }
}
