import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/l10n/locale_notifier.dart';
import '../../../core/l10n/report_ui_labels.dart';
import '../../../core/services/api_models.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/utils/markdown_formatter.dart';
import 'package:mednarrate/l10n/app_localizations.dart';
import '../models/report_model.dart';
import 'translation_parameter_name.dart';

class ClinicalViewTab extends StatelessWidget {
  final ReportModel report;
  final ReportAnalysisModel? analysis;
  final ComparePreviousResult? comparison;
  final TranslationModel? translation;

  const ClinicalViewTab({
    super.key,
    required this.report,
    this.analysis,
    this.comparison,
    this.translation,
  });

  String _label(String key, {required String fallback}) {
    final t = translation;
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

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final summary = Helpers.sanitizeDisplayText(
      translation?.clinicianSummary ??
          analysis?.translatedClinicianSummary ??
          report.translatedClinicalSummary ??
          analysis?.clinicianSummary ??
          report.clinicalSummary ??
          AppLocalizations.of(context)!.noClinicalSummary,
    );

    final rawLabs = analysis?.structuredLabValues ?? [];
    final labs =
        rawLabs.where((l) => !Helpers.isMetadataParameter(l.testName)).toList();
    final meds = analysis?.medications ?? [];

    // Merge translated medications if available
    final List<Map<String, dynamic>> displayMeds = meds.map((m) {
      if (translation != null && translation!.medicationsJson.isNotEmpty) {
        final origName = m['medication_name']?.toString();
        final tMed = translation!.medicationsJson.firstWhere(
          (t) => t['medication_name']?.toString() == origName,
          orElse: () => <String, dynamic>{},
        );
        if (tMed.isNotEmpty) {
          return {
            ...m,
            'medication_name':
                tMed['translated_medication_name'] ?? m['medication_name'],
            'dosage': tMed['translated_dosage'] ?? m['dosage'],
            'frequency': tMed['translated_frequency'] ?? m['frequency'],
            'times_of_day':
                tMed['translated_times_of_day'] ?? m['times_of_day'],
            'instructions':
                tMed['translated_instructions'] ?? m['instructions'],
          };
        }
      }
      return m;
    }).toList();

    final rawAbnormal = analysis?.abnormalFindings ??
        labs
            .where((l) => l.flag != 'normal' && l.flag != 'not_classified')
            .toList();

    final abnormalList = rawAbnormal.map((item) {
      if (translation != null && translation!.findingsJson.isNotEmpty) {
        String name = '';
        if (item is LabValue) {
          name = item.testName;
        } else if (item is Map<String, dynamic>) {
          name = item['test_name']?.toString() ??
              item['parameter']?.toString() ??
              item['original_name']?.toString() ??
              '';
        }

        final tFinding = translation!.findingsJson.firstWhere(
          (t) => t['test_name']?.toString() == name,
          orElse: () => <String, dynamic>{},
        );

        if (tFinding.isNotEmpty) {
          if (item is LabValue) {
            return {
              'test_name': name,
              'value': item.value,
              'unit': item.unit,
              'flag': item.flag,
              'ref_low': item.refLow,
              'ref_high': item.refHigh,
              'explanation': tFinding['translated_explanation'],
            };
          } else if (item is Map<String, dynamic>) {
            return {
              ...item,
              'explanation':
                  tFinding['translated_explanation'] ?? item['explanation'],
            };
          }
        }
      }
      return item;
    }).where((item) {
      if (item is LabValue) return !Helpers.isMetadataParameter(item.testName);
      if (item is Map<String, dynamic>) {
        final name = item['test_name']?.toString() ??
            item['parameter']?.toString() ??
            item['original_name']?.toString() ??
            '';
        return !Helpers.isMetadataParameter(name);
      }
      return true;
    }).toList();

    final diagnoses = analysis?.entities
            .where((e) =>
                e['entity_group'] == 'Diagnosis' ||
                e['category'] == 'Diagnosis')
            .toList() ??
        [];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Clinical Overview Header Card
          _buildClinicalHeader(context, report, analysis),

          const SizedBox(height: 20),

          // 2. Clinical Executive Summary
          Text(
            _label('label_clinical_report_heading',
                fallback: 'Clinical Executive Summary'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
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
                        _aiAttributionLabel(),
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

          // 3. Key Clinical Findings / Noteworthy Alerts
          Text(
            _label('section_key_clinical_findings',
                fallback: 'Key Clinical Findings'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          if (abnormalList.isEmpty)
            _buildInfoBox(
                context,
                _label('label_no_key_findings',
                    fallback:
                        'No out-of-range clinical parameters flagged in this report.'))
          else
            ...abnormalList.map((item) {
              if (item is LabValue) {
                return ClinicalViewTab.buildAbnormalFindingRow(
                    context,
                    item.testName,
                    '${item.value} ${item.unit}',
                    item.flag,
                    item.refLow,
                    item.refHigh,
                    null,
                    translation);
              } else if (item is Map<String, dynamic>) {
                return ClinicalViewTab.buildAbnormalFindingRow(
                  context,
                  item['test_name']?.toString() ??
                      item['parameter']?.toString() ??
                      AppLocalizations.of(context)!.findingFallback,
                  '${item['value'] ?? ''} ${item['unit'] ?? ''}',
                  item['flag']?.toString() ?? 'HIGH',
                  (item['ref_low'] as num?)?.toDouble(),
                  (item['ref_high'] as num?)?.toDouble(),
                  item['explanation']?.toString(),
                  translation,
                );
              }
              return const SizedBox.shrink();
            }),

          const SizedBox(height: 24),

          // 4. Laboratory Results Table
          Text(
            _label('chip_lab_results', fallback: 'Laboratory Results'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          if (labs.isEmpty)
            _buildInfoBox(
                context,
                _label('label_no_lab_results',
                    fallback:
                        'No laboratory results found in structured analysis.'))
          else
            ClinicalViewTab.buildLabTable(context, labs, translation),

          const SizedBox(height: 24),

          // 5. Medications Table
          Text(
            _label('section_reported_medications',
                fallback: 'Reported Medications'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          if (displayMeds.isEmpty)
            _buildInfoBox(
                context,
                _label('label_no_medications',
                    fallback: 'No medications recorded in report data.'))
          else
            ClinicalViewTab.buildMedicationsTable(
                context, displayMeds, translation),

          const SizedBox(height: 24),

          // 6. Diagnoses & Extracted Findings
          if (diagnoses.isNotEmpty) ...[
            Text(
              _label('section_diagnoses', fallback: 'Diagnoses & Findings'),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: theme.cardColor,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                    color: Theme.of(context).colorScheme.outlineVariant),
              ),
              child: Column(
                children: diagnoses
                    .map((d) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            children: [
                              Icon(
                                Icons.medical_information_outlined,
                                size: 18,
                                color: AppColors.primary,
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  d['word']?.toString() ?? '',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.bold, fontSize: 14),
                                ),
                              ),
                            ],
                          ),
                        ))
                    .toList(),
              ),
            ),
            const SizedBox(height: 24),
          ],

          // 7. Historical Comparison
          Text(
            _label('section_historical_comparison',
                fallback: 'Historical Comparison'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          ClinicalViewTab.buildHistoricalComparison(
              context, comparison, translation),

          const SizedBox(height: 24),

          // 8. Source & Validation Metadata
          Text(
            _label('section_source_validation',
                fallback: 'Source & Validation'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          ClinicalViewTab.buildValidationMetadataCard(
              context, report, analysis, translation),

          const SizedBox(height: 40),
        ],
      ),
    );
  }

  String _aiAttributionLabel() {
    final provider = analysis?.llmProvider?.toLowerCase() ?? '';
    if (provider.contains('gemini') || provider.contains('vertex')) {
      return _label('label_generated_by_gemini',
          fallback: 'Generated by Gemini AI');
    } else if (provider.contains('ollama')) {
      return _label('label_generated_by_ollama',
          fallback: 'Generated by Ollama');
    } else if (provider.contains('fallback') || provider.contains('local')) {
      return _label('label_generated_by_local_fallback',
          fallback: 'Generated by local fallback model');
    }
    return _label('label_generated_offline',
        fallback: 'Generated in offline mode');
  }

  /// Shows the real automated-verification outcome stored with the analysis
  /// ("verified" / "invalid" / not yet verified) instead of a fixed label.
  Widget _buildValidationBadge(ReportAnalysisModel? analysis) {
    final status = (analysis?.verificationStatus ?? '').toLowerCase();
    late final String key;
    late final String fallback;
    late final Color color;
    if (status == 'verified') {
      key = 'label_validation_passed';
      fallback = 'PASSED';
      color = AppColors.success;
    } else if (status == 'invalid') {
      key = 'label_validation_failed';
      fallback = 'NEEDS REVIEW';
      color = AppColors.error;
    } else {
      key = 'label_validation_pending';
      fallback = 'NOT VERIFIED';
      color = AppColors.warning;
    }
    final text =
        '${_label('label_validation', fallback: 'Validation')}: ${_label(key, fallback: fallback)}';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text,
        style:
            TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: color),
      ),
    );
  }

  Widget _buildClinicalHeader(
      BuildContext context, ReportModel report, ReportAnalysisModel? analysis) {
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
                backgroundColor: AppColors.accentTeal.withValues(alpha: 0.1),
                child: const Icon(Icons.medical_services_outlined,
                    color: AppColors.accentTeal, size: 26),
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
                    ),
                    Text(
                      '${_label('label_hospital', fallback: 'Hospital')}: ${report.hospital.isNotEmpty ? report.hospital : _label('label_unspecified', fallback: "Unspecified")} • ${_label('label_date', fallback: 'Date')}: ${Formatters.formatDate(report.reportDate, translation?.language ?? localeModeNotifier.value.languageCode)}',
                      style: TextStyle(
                          fontSize: 12.5,
                          color: theme.colorScheme.onSurface
                              .withValues(alpha: 0.6)),
                    ),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.accentTeal.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            '${_label('label_status', fallback: 'Status')}: ${_label('label_status_${report.processingStatus}', fallback: report.processingStatus.toUpperCase())}',
                            style: const TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: AppColors.accentTeal),
                          ),
                        ),
                        _buildValidationBadge(analysis),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  static Widget buildAbnormalFindingRow(
      BuildContext context,
      String testName,
      String result,
      String flag,
      double? refLow,
      double? refHigh,
      String? explanation,
      TranslationModel? translation) {
    final theme = Theme.of(context);
    final flagLower = flag.toLowerCase();

    Color color = Colors.orange;
    String statusTitle =
        effectiveReportUiLabels(translation)['label_not_classified'] ?? 'No reference range';
    if (flagLower == 'high') {
      color = Colors.redAccent;
      statusTitle = effectiveReportUiLabels(translation)['label_high'] ?? 'High';
    } else if (flagLower == 'low') {
      color = Colors.orange;
      statusTitle = effectiveReportUiLabels(translation)['label_low'] ?? 'Low';
    } else if (flagLower == 'critical') {
      color = AppColors.warning;
      statusTitle = effectiveReportUiLabels(translation)['label_critical'] ?? 'Critical';
    } else if (flagLower == 'normal') {
      color = const Color(0xFF00C48C);
      statusTitle = effectiveReportUiLabels(translation)['label_normal'] ?? 'Normal';
    }

    String refText =
        effectiveReportUiLabels(translation)['label_not_provided'] ?? 'Not provided in report';
    if (refLow != null && refHigh != null) {
      refText = '$refLow – $refHigh';
    } else if (refLow != null) {
      refText = '> $refLow';
    } else if (refHigh != null) {
      refText = '< $refHigh';
    }

    final reason = (explanation != null && explanation.isNotEmpty)
        ? explanation
        : (effectiveReportUiLabels(translation)['label_key_finding_expansion_patient'] ??
            'Result measured outside expected laboratory bounds.');

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(translatedParameterName(testName, translation),
                    style: const TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 16)),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8)),
                child: Text(statusTitle,
                    style: TextStyle(
                        color: color,
                        fontWeight: FontWeight.bold,
                        fontSize: 11)),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text('${effectiveReportUiLabels(translation)['label_result'] ?? 'Result'}: $result',
              style:
                  const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(
              '${effectiveReportUiLabels(translation)['label_reported_range'] ?? 'Reported range'}: $refText',
              style: TextStyle(
                  fontSize: 13,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.8))),
          const SizedBox(height: 2),
          Text(
              '${effectiveReportUiLabels(translation)['label_status'] ?? 'Status'}: $statusTitle',
              style: TextStyle(
                  fontSize: 12, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.04),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                    effectiveReportUiLabels(translation)['label_why_it_was_flagged'] ??
                        'Why it was flagged:',
                    style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: theme.colorScheme.primary)),
                const SizedBox(height: 2),
                Text(reason,
                    style: TextStyle(
                        fontSize: 12.5,
                        color:
                            theme.colorScheme.onSurface.withValues(alpha: 0.85),
                        height: 1.3)),
              ],
            ),
          ),
          const SizedBox(height: 6),
          Text(
              effectiveReportUiLabels(translation)['label_source_latest_report'] ??
                  'Source: Uploaded report',
              style: TextStyle(
                  fontSize: 10,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5))),
        ],
      ),
    );
  }

  static Widget buildLabTable(BuildContext context, List<LabValue> labs,
      TranslationModel? translation) {
    final theme = Theme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            headingRowColor: WidgetStateProperty.all(
                theme.colorScheme.onSurface.withValues(alpha: 0.04)),
            columns: [
              DataColumn(
                  label: Text(
                      effectiveReportUiLabels(translation)['label_parameter'] ?? 'Parameter',
                      style: const TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(
                  label: Text(effectiveReportUiLabels(translation)['label_result'] ?? 'Result',
                      style: const TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(
                  label: Text(effectiveReportUiLabels(translation)['label_unit'] ?? 'Unit',
                      style: const TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(
                  label: Text(
                      effectiveReportUiLabels(translation)['label_reference_range'] ??
                          'Reference Range',
                      style: const TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(
                  label: Text(effectiveReportUiLabels(translation)['label_status'] ?? 'Status',
                      style: const TextStyle(fontWeight: FontWeight.bold))),
            ],
            rows: labs.map((l) {
              String ref =
                  effectiveReportUiLabels(translation)['label_not_provided'] ?? 'Not provided';
              if (l.refLow != null && l.refHigh != null) {
                ref = '${l.refLow} – ${l.refHigh}';
              }
              if (l.referenceSource == 'general_provisional') {
                ref = '$ref ${AppLocalizations.of(context)!.refGeneralProvisional}';
              }
              String flagStr = effectiveReportUiLabels(translation)['label_not_classified']
                      ?.toUpperCase() ??
                  "NO REFERENCE RANGE";
              Color c = theme.colorScheme.onSurface;
              final String originalFlag = l.flag.toUpperCase();
              if (originalFlag == 'HIGH') {
                c = Colors.redAccent;
                flagStr = effectiveReportUiLabels(translation)['label_high']?.toUpperCase() ??
                    "HIGH";
              }
              if (originalFlag == 'LOW') {
                c = Colors.orange;
                flagStr =
                    effectiveReportUiLabels(translation)['label_low']?.toUpperCase() ?? "LOW";
              }
              if (originalFlag == 'NORMAL') {
                c = const Color(0xFF00C48C);
                flagStr =
                    effectiveReportUiLabels(translation)['label_normal']?.toUpperCase() ??
                        "NORMAL";
              }
              if (l.referenceSource == 'general_provisional') {
                flagStr =
                    '$flagStr · ${AppLocalizations.of(context)!.provisionalWord.toUpperCase()}';
              }
              if (originalFlag == 'CRITICAL') {
                c = Colors.red.shade900;
                flagStr =
                    effectiveReportUiLabels(translation)['label_critical']?.toUpperCase() ??
                        "CRITICAL";
              }

              return DataRow(cells: [
                DataCell(Text(translatedParameterName(l.testName, translation),
                    style: const TextStyle(fontWeight: FontWeight.w600))),
                DataCell(Text('${l.value}')),
                DataCell(Text(l.unit)),
                DataCell(Text(ref)),
                DataCell(Text(flagStr,
                    style: TextStyle(
                        color: c, fontWeight: FontWeight.bold, fontSize: 12))),
              ]);
            }).toList(),
          ),
        ),
      ),
    );
  }

  static Widget buildMedicationsTable(BuildContext context,
      List<Map<String, dynamic>> meds, TranslationModel? translation) {
    final theme = Theme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            headingRowColor: WidgetStateProperty.all(
                theme.colorScheme.onSurface.withValues(alpha: 0.04)),
            columns: [
              DataColumn(
                  label: Text(
                      effectiveReportUiLabels(translation)['chip_medications'] ?? 'Medication',
                      style: const TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(
                  label: Text(effectiveReportUiLabels(translation)['label_dose'] ?? 'Dosage',
                      style: const TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(
                  label: Text(
                      effectiveReportUiLabels(translation)['label_frequency'] ?? 'Frequency',
                      style: const TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(
                  label: Text(effectiveReportUiLabels(translation)['label_timing'] ?? 'Timing',
                      style: const TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(
                  label: Text(
                      effectiveReportUiLabels(translation)['label_source_document'] ??
                          'Provenance',
                      style: const TextStyle(fontWeight: FontWeight.bold))),
            ],
            rows: meds.map((m) {
              final name = m['medication_name']?.toString() ?? 'Medication';
              final dose = m['dosage']?.toString() ??
                  effectiveReportUiLabels(translation)['label_unspecified'] ??
                  'Not specified';
              final freq = m['frequency']?.toString() ??
                  effectiveReportUiLabels(translation)['label_unspecified'] ??
                  'Not specified';
              final times = List<String>.from(m['times_of_day'] ?? []);
              final timing = times.isNotEmpty
                  ? times.join(', ')
                  : effectiveReportUiLabels(translation)['label_unspecified'] ??
                      'Not specified';
              final prov = m['provenance']?.toString() ??
                  effectiveReportUiLabels(translation)['label_report_extracted'] ??
                  'Report Extracted';

              return DataRow(cells: [
                DataCell(Text(name,
                    style: const TextStyle(fontWeight: FontWeight.bold))),
                DataCell(Text(dose)),
                DataCell(Text(freq)),
                DataCell(Text(timing)),
                DataCell(Text(prov,
                    style: const TextStyle(fontSize: 11, color: Colors.grey))),
              ]);
            }).toList(),
          ),
        ),
      ),
    );
  }

  static Widget buildHistoricalComparison(BuildContext context,
      ComparePreviousResult? comp, TranslationModel? translation) {
    final theme = Theme.of(context);
    if (comp == null || !comp.comparable) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: theme.cardColor,
          borderRadius: BorderRadius.circular(14),
          border:
              Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        ),
        child: Text(
          (comp?.reason == 'no_previous_report' || comp?.reason == null)
              ? (effectiveReportUiLabels(translation)['label_no_previous_report'] ??
                  'No previous comparable report is available for baseline comparison.')
              : (effectiveReportUiLabels(translation)['label_${comp?.reason}'] ??
                  comp?.reason ??
                  ''),
          style: TextStyle(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              fontSize: 14),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (comp.narrativeSummary != null &&
              comp.narrativeSummary!.isNotEmpty)
            Text(comp.narrativeSummary!,
                style: const TextStyle(fontSize: 14, height: 1.4)),
          const SizedBox(height: 10),
          ...comp.comparedFindings.map((f) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                          effectiveReportUiLabels(translation)['param_${f['parameter']}'] ??
                              f['parameter']?.toString() ??
                              (effectiveReportUiLabels(translation)['label_parameter'] ??
                                  'Test'),
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                    ),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Text(
                          '${f['previous_value']} ➔ ${f['current_value']} ${f['unit']} (${f['change']})',
                          textAlign: TextAlign.end,
                          style: const TextStyle(fontSize: 13)),
                    ),
                  ],
                ),
              )),
        ],
      ),
    );
  }

  static Widget buildValidationMetadataCard(
      BuildContext context, ReportModel report, ReportAnalysisModel? analysis,
      [TranslationModel? translation]) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Column(
        children: [
          ClinicalViewTab.buildMetaRow(
              context,
              effectiveReportUiLabels(translation)['label_source_document'] ??
                  'Source Document',
              report.fileName),
          ClinicalViewTab.buildMetaRow(
              context,
              effectiveReportUiLabels(translation)['label_report_date'] ?? 'Report Date',
              Formatters.formatDate(
                  report.reportDate, translation?.language ?? localeModeNotifier.value.languageCode)),
          ClinicalViewTab.buildMetaRow(
              context,
              effectiveReportUiLabels(translation)['chip_report_type'] ?? 'Report Type',
              effectiveReportUiLabels(translation)['chip_${report.reportType}'] ??
                  Helpers.reportTypeLabelIn(
                      report.reportType,
                      translation != null && translation.language != 'en'
                          ? translation.language
                          : localeModeNotifier.value.languageCode)),
          ClinicalViewTab.buildMetaRow(
              context,
              effectiveReportUiLabels(translation)['label_rag_search_index'] ??
                  'RAG Search Index',
              effectiveReportUiLabels(translation)['label_active_retriever'] ??
                  'Active (TF-IDF Lexical Retriever)'),
          ClinicalViewTab.buildMetaRow(
              context,
              effectiveReportUiLabels(translation)['label_medical_validation'] ??
                  'Medical Validation',
              effectiveReportUiLabels(translation)['label_passed_rules'] ??
                  'Passed (Grounding & Range Rules)'),
        ],
      ),
    );
  }

  static Widget buildMetaRow(BuildContext context, String label, String value) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            flex: 2,
            child: Text(label,
                style: TextStyle(
                    fontSize: 13,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6))),
          ),
          const SizedBox(width: 12),
          Expanded(
            flex: 3,
            child: Text(value,
                textAlign: TextAlign.end,
                style: const TextStyle(
                    fontSize: 13, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoBox(BuildContext context, String text) {
    final theme = Theme.of(context);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Text(text,
          style: TextStyle(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.54),
              fontSize: 14)),
    );
  }
}
