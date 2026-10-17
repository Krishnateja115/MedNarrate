import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../reports/models/report_model.dart';
import '../../../core/routing/routes.dart';
import 'lab_result_row.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/l10n/report_ui_labels.dart';
import '../../../core/utils/helpers.dart';
import 'package:mednarrate/l10n/app_localizations.dart';
import '../../../core/services/api_models.dart';
import 'translation_parameter_name.dart';

class LabResultsTab extends StatefulWidget {
  final ReportModel report;
  final TranslationModel? translation;
  final List<EvidenceSource> evidenceSources;

  const LabResultsTab({
    super.key,
    required this.report,
    this.translation,
    this.evidenceSources = const [],
  });

  @override
  State<LabResultsTab> createState() => _LabResultsTabState();
}

class _LabResultsTabState extends State<LabResultsTab> {
  String _searchQuery = '';

  final Map<String, List<String>> _categories = {
    'CBC': ['Hemoglobin', 'WBC', 'RBC', 'Platelets', 'Hematocrit'],
    'Lipid Panel': [
      'Total Cholesterol',
      'LDL Cholesterol',
      'HDL Cholesterol',
      'Triglycerides'
    ],
    'Liver Function': ['ALT', 'AST', 'ALP', 'Bilirubin'],
    'Kidney Function': ['Creatinine', 'BUN', 'eGFR'],
    'Vitamins & Minerals': [
      'Vitamin D',
      'Vitamin B12',
      'Iron',
      'Calcium',
      'Potassium'
    ],
  };

  /// "What is {name}?" - the translated template carries a {name} placeholder
  /// because word order differs between languages; older cached translations
  /// stored just "What is", so both forms are supported.
  String _whatIsText(String name) {
    final template = effectiveReportUiLabels(widget.translation)['label_what_is'];
    if (template == null || template.trim().isEmpty) return 'What is $name?';
    if (template.contains('{name}')) return template.replaceAll('{name}', name);
    return '$template $name?';
  }

  void _showParameterDetails(
      BuildContext context, Map<String, dynamic> metric) {
    final String parameterName = metric['parameter']?.toString() ?? '';
    final String translatedName =
        translatedParameterName(parameterName, widget.translation);
    final excerpts = widget.evidenceSources
        .where((source) =>
            source.finding.toLowerCase() == parameterName.toLowerCase())
        .expand((source) => source.sources)
        .toList();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) {
        return SingleChildScrollView(
          child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(translatedName,
                  style: const TextStyle(
                      fontSize: 22, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text(
                _whatIsText(translatedName),
                style: TextStyle(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                AppLocalizations.of(context)!
                    .labMeasuresDesc('${metric['parameter']}'),
                style: TextStyle(
                    color: Theme.of(context)
                        .colorScheme
                        .onSurface
                        .withValues(alpha: 0.7)),
              ),
              if (excerpts.isNotEmpty) ...[
                const SizedBox(height: 16),
                Text(AppLocalizations.of(context)!.textDetectedInReport,
                    style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 6),
                for (final excerpt in excerpts)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: SelectableText(excerpt),
                  ),
                Text(AppLocalizations.of(context)!.checkAgainstOriginalOcr),
              ],
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: FilledButton.icon(
                  onPressed: () {
                    Navigator.pop(context);
                    context.push(Routes.originalReport, extra: {
                      'reportId': widget.report.id,
                      'fileName': widget.report.fileName,
                    });
                  },
                  icon: const Icon(Icons.description_outlined),
                  label: Text(AppLocalizations.of(context)!.viewOriginalReport),
                ),
              ),
            ],
          ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    List<Map<String, dynamic>> filteredMetrics =
        widget.report.metrics.where((m) {
      final paramName = m['parameter'].toString();
      if (Helpers.isMetadataParameter(paramName)) {
        return false;
      }
      return paramName.toLowerCase().contains(_searchQuery.toLowerCase());
    }).toList();

    final defaultCat =
        effectiveReportUiLabels(widget.translation)['label_uncategorized'] ?? 'Uncategorized';
    Map<String, List<Map<String, dynamic>>> grouped = {defaultCat: []};
    for (var m in filteredMetrics) {
      String cat = defaultCat;
      for (var entry in _categories.entries) {
        if (entry.value.any((v) =>
            v.toLowerCase() == m['parameter'].toString().toLowerCase())) {
          cat = effectiveReportUiLabels(widget.translation)[
                  'label_cat_${entry.key.toLowerCase().replaceAll(' ', '_')}'] ??
              entry.key;
          break;
        }
      }
      if (!grouped.containsKey(cat)) grouped[cat] = [];
      grouped[cat]!.add(m);
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: TextField(
            onChanged: (v) => setState(() => _searchQuery = v),
            decoration: InputDecoration(
              hintText:
                  effectiveReportUiLabels(widget.translation)['label_search_parameters'] ??
                      AppLocalizations.of(context)!.searchParameters,
              prefixIcon: const Icon(Icons.search),
              filled: true,
              fillColor: Theme.of(context).cardColor,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
            ),
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: grouped.keys.length,
            itemBuilder: (context, index) {
              String cat = grouped.keys.elementAt(index);
              List<Map<String, dynamic>> items = grouped[cat]!;
              if (items.isEmpty) return const SizedBox.shrink();

              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: Text(cat,
                        style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: AppColors.primary)),
                  ),
                  ...items.map((m) {
                    final double val = (m['value'] is num)
                        ? (m['value'] as num).toDouble()
                        : 0.0;
                    final double? minR = (m['min_range'] is num)
                        ? (m['min_range'] as num).toDouble()
                        : ((m['ref_low'] is num)
                            ? (m['ref_low'] as num).toDouble()
                            : null);
                    final double? maxR = (m['max_range'] is num)
                        ? (m['max_range'] as num).toDouble()
                        : ((m['ref_high'] is num)
                            ? (m['ref_high'] as num).toDouble()
                            : null);
                    final String flag =
                        m['flag']?.toString() ?? 'not_classified';

                    final String parameterName =
                        m['parameter']?.toString() ?? '';
                    final String translatedName = translatedParameterName(
                        parameterName, widget.translation);

                    return LabResultRow(
                      parameter: translatedName,
                      unit: m['unit'] ?? '',
                      value: val,
                      minRange: minR,
                      maxRange: maxR,
                      flag: flag,
                      isProvisional:
                          m['reference_source'] == 'general_provisional',
                      translation: widget.translation,
                      onTap: () => _showParameterDetails(context, m),
                    );
                  }),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}
