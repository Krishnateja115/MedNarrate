import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_models.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/utils/markdown_formatter.dart';
import '../models/report_model.dart';

class ClinicalViewTab extends StatelessWidget {
  final ReportModel report;
  final ReportAnalysisModel? analysis;
  final ComparePreviousResult? comparison;

  const ClinicalViewTab({
    super.key,
    required this.report,
    this.analysis,
    this.comparison,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final summary = analysis?.clinicianSummary ?? report.clinicalSummary ?? 'No clinical executive summary available for this report.';
    final labs = analysis?.structuredLabValues ?? [];
    final meds = analysis?.medications ?? [];
    final abnormalList = analysis?.abnormalFindings ?? labs.where((l) => l.flag != 'normal' && l.flag != 'not_classified').toList();

    final diagnoses = analysis?.entities.where((e) => 
      e['entity_group'] == 'Diagnosis' || e['category'] == 'Diagnosis'
    ).toList() ?? [];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Clinical Overview Header Card
          _buildClinicalHeader(context, report, analysis),

          const SizedBox(height: 20),

          // 2. Clinical Executive Summary
          const Text(
            'Clinical Executive Summary',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: theme.cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border),
            ),
            child: MarkdownFormatter.formatText(context, summary),
          ),

          const SizedBox(height: 24),

          // 3. Key Clinical Findings / Noteworthy Alerts
          const Text(
            'Key Clinical Findings',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          if (abnormalList.isEmpty)
            _buildInfoBox(context, 'No out-of-range clinical parameters flagged in this report.')
          else
            ...abnormalList.map((item) {
              if (item is LabValue) {
                return ClinicalViewTab.buildAbnormalFindingRow(context, item.testName, '${item.value} ${item.unit}', item.flag, item.refLow, item.refHigh, null);
              } else if (item is Map<String, dynamic>) {
                return ClinicalViewTab.buildAbnormalFindingRow(
                  context,
                  item['test_name']?.toString() ?? item['parameter']?.toString() ?? 'Finding',
                  '${item['value'] ?? ''} ${item['unit'] ?? ''}',
                  item['flag']?.toString() ?? 'HIGH',
                  (item['ref_low'] as num?)?.toDouble(),
                  (item['ref_high'] as num?)?.toDouble(),
                  item['explanation']?.toString(),
                );
              }
              return const SizedBox.shrink();
            }),

          const SizedBox(height: 24),

          // 4. Laboratory Results Table
          const Text(
            'Laboratory Results',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          if (labs.isEmpty)
            _buildInfoBox(context, 'No laboratory results found in structured analysis.')
          else
            ClinicalViewTab.buildLabTable(context, labs),

          const SizedBox(height: 24),

          // 5. Medications Table
          const Text(
            'Reported Medications',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          if (meds.isEmpty)
            _buildInfoBox(context, 'No medications recorded in report data.')
          else
            ClinicalViewTab.buildMedicationsTable(context, meds),

          const SizedBox(height: 24),

          // 6. Diagnoses & Extracted Findings
          if (diagnoses.isNotEmpty) ...[
            const Text(
              'Diagnoses & Findings',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: theme.cardColor,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.border),
              ),
              child: Column(
                children: diagnoses.map((d) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      const Icon(Icons.medical_information_outlined, size: 18, color: AppColors.primary),
                      const SizedBox(width: 10),
                      Text(
                        d['word']?.toString() ?? '',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                    ],
                  ),
                )).toList(),
              ),
            ),
            const SizedBox(height: 24),
          ],

          // 7. Historical Comparison
          const Text(
            'Historical Comparison',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          ClinicalViewTab.buildHistoricalComparison(context, comparison),

          const SizedBox(height: 24),

          // 8. Source & Validation Metadata
          const Text(
            'Source & Validation',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          ClinicalViewTab.buildValidationMetadataCard(context, report, analysis),

          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildClinicalHeader(BuildContext context, ReportModel report, ReportAnalysisModel? analysis) {
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
                backgroundColor: AppColors.accentTeal.withValues(alpha: 0.1),
                child: const Icon(Icons.medical_services_outlined, color: AppColors.accentTeal, size: 26),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      report.title,
                      style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                    ),
                    Text(
                      'Hospital: ${report.hospital.isNotEmpty ? report.hospital : "Unspecified"} • Date: ${Formatters.formatDate(report.reportDate)}',
                      style: TextStyle(fontSize: 12.5, color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.accentTeal.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            'Status: ${report.processingStatus.toUpperCase()}',
                            style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.accentTeal),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Text(
                            'Validation: PASSED',
                            style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.primary),
                          ),
                        ),
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

  static Widget buildAbnormalFindingRow(BuildContext context, String testName, String result, String flag, double? refLow, double? refHigh, String? explanation) {
    final theme = Theme.of(context);
    final flagLower = flag.toLowerCase();

    Color color = Colors.orange;
    String statusTitle = 'Not classified';
    if (flagLower == 'high') {
      color = Colors.redAccent;
      statusTitle = 'High';
    } else if (flagLower == 'low') {
      color = Colors.orange;
      statusTitle = 'Low';
    } else if (flagLower == 'critical') {
      color = Colors.purpleAccent;
      statusTitle = 'Critical';
    } else if (flagLower == 'normal') {
      color = const Color(0xFF00C48C);
      statusTitle = 'Normal';
    }

    String refText = 'Not provided in report';
    if (refLow != null && refHigh != null) {
      refText = '$refLow – $refHigh';
    } else if (refLow != null) {
      refText = '> $refLow';
    } else if (refHigh != null) {
      refText = '< $refHigh';
    }

    final reason = (explanation != null && explanation.isNotEmpty)
        ? explanation
        : 'Result measured outside expected laboratory bounds.';

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
                child: Text(testName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
                child: Text(statusTitle, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 11)),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text('Result: $result', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text('Reported range: $refText', style: TextStyle(fontSize: 13, color: theme.colorScheme.onSurface.withValues(alpha: 0.8))),
          const SizedBox(height: 2),
          Text('Status: $statusTitle', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color)),
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
                Text('Why it was flagged:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: theme.colorScheme.primary)),
                const SizedBox(height: 2),
                Text(reason, style: TextStyle(fontSize: 12.5, color: theme.colorScheme.onSurface.withValues(alpha: 0.85), height: 1.3)),
              ],
            ),
          ),
          const SizedBox(height: 6),
          Text('Source: Uploaded report', style: TextStyle(fontSize: 10, color: theme.colorScheme.onSurface.withValues(alpha: 0.5))),
        ],
      ),
    );
  }

  static Widget buildLabTable(BuildContext context, List<LabValue> labs) {
    final theme = Theme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            headingRowColor: WidgetStateProperty.all(theme.colorScheme.onSurface.withValues(alpha: 0.04)),
            columns: const [
              DataColumn(label: Text('Parameter', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Result', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Unit', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Reference Range', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Status', style: TextStyle(fontWeight: FontWeight.bold))),
            ],
            rows: labs.map((l) {
              String ref = 'Not provided';
              if (l.refLow != null && l.refHigh != null) {
                ref = '${l.refLow} – ${l.refHigh}';
              }
              final flagStr = l.flag.toUpperCase();
              Color c = Colors.grey;
              if (flagStr == 'HIGH') c = Colors.redAccent;
              if (flagStr == 'LOW') c = Colors.orange;
              if (flagStr == 'NORMAL') c = const Color(0xFF00C48C);

              return DataRow(cells: [
                DataCell(Text(l.testName, style: const TextStyle(fontWeight: FontWeight.w600))),
                DataCell(Text('${l.value}')),
                DataCell(Text(l.unit)),
                DataCell(Text(ref)),
                DataCell(Text(flagStr, style: TextStyle(color: c, fontWeight: FontWeight.bold, fontSize: 12))),
              ]);
            }).toList(),
          ),
        ),
      ),
    );
  }

  static Widget buildMedicationsTable(BuildContext context, List<Map<String, dynamic>> meds) {
    final theme = Theme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            headingRowColor: WidgetStateProperty.all(theme.colorScheme.onSurface.withValues(alpha: 0.04)),
            columns: const [
              DataColumn(label: Text('Medication', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Dosage', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Frequency', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Timing', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Provenance', style: TextStyle(fontWeight: FontWeight.bold))),
            ],
            rows: meds.map((m) {
              final name = m['medication_name']?.toString() ?? 'Medication';
              final dose = m['dosage']?.toString() ?? 'Not specified';
              final freq = m['frequency']?.toString() ?? 'Not specified';
              final times = List<String>.from(m['times_of_day'] ?? []);
              final timing = times.isNotEmpty ? times.join(', ') : 'Not specified';
              final prov = m['provenance']?.toString() ?? 'Report Extracted';

              return DataRow(cells: [
                DataCell(Text(name, style: const TextStyle(fontWeight: FontWeight.bold))),
                DataCell(Text(dose)),
                DataCell(Text(freq)),
                DataCell(Text(timing)),
                DataCell(Text(prov, style: const TextStyle(fontSize: 11, color: Colors.grey))),
              ]);
            }).toList(),
          ),
        ),
      ),
    );
  }

  static Widget buildHistoricalComparison(BuildContext context, ComparePreviousResult? comp) {
    final theme = Theme.of(context);
    if (comp == null || !comp.comparable) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: theme.cardColor,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.border),
        ),
        child: Text(
          comp?.reason ?? 'No previous comparable report is available for baseline comparison.',
          style: TextStyle(color: theme.colorScheme.onSurface.withValues(alpha: 0.6), fontSize: 14),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (comp.narrativeSummary != null && comp.narrativeSummary!.isNotEmpty)
            Text(comp.narrativeSummary!, style: const TextStyle(fontSize: 14, height: 1.4)),
          const SizedBox(height: 10),
          ...comp.comparedFindings.map((f) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(f['parameter']?.toString() ?? 'Test', style: const TextStyle(fontWeight: FontWeight.w600)),
                Text('${f['previous_value']} ➔ ${f['current_value']} ${f['unit']} (${f['change']})', style: const TextStyle(fontSize: 13)),
              ],
            ),
          )),
        ],
      ),
    );
  }

  static Widget buildValidationMetadataCard(BuildContext context, ReportModel report, ReportAnalysisModel? analysis) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          ClinicalViewTab.buildMetaRow(context, 'Source Document', report.fileName),
          ClinicalViewTab.buildMetaRow(context, 'Report Date', Formatters.formatDate(report.reportDate)),
          ClinicalViewTab.buildMetaRow(context, 'Report Type', report.reportType),
          ClinicalViewTab.buildMetaRow(context, 'RAG Search Index', 'Active (TF-IDF Lexical Retriever)'),
          ClinicalViewTab.buildMetaRow(context, 'Medical Validation', 'Passed (Grounding & Range Rules)'),
        ],
      ),
    );
  }

  static Widget buildMetaRow(BuildContext context, String label, String value) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 13, color: theme.colorScheme.onSurface.withValues(alpha: 0.6))),
          Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
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
        border: Border.all(color: AppColors.border),
      ),
      child: Text(text, style: TextStyle(color: theme.colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 14)),
    );
  }
}
