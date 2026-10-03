import 'package:flutter/material.dart';
import '../../reports/models/report_model.dart';
import 'lab_result_row.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/utils/helpers.dart';
import 'package:mednarrate/l10n/app_localizations.dart';
import '../../../core/services/api_models.dart';

class LabResultsTab extends StatefulWidget {
  final ReportModel report;
  final TranslationModel? translation;

  const LabResultsTab({super.key, required this.report, this.translation});

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

  void _showParameterDetails(
      BuildContext context, Map<String, dynamic> metric) {
    final String parameterName = metric['parameter']?.toString() ?? '';
    final String translatedName = widget.translation?.uiLabels['param_$parameterName'] ?? parameterName;

    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) {
        return Padding(
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
                '${widget.translation?.uiLabels['label_what_is'] ?? 'What is'} $translatedName?',
                style: TextStyle(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'This measures ${metric['parameter']} in your medical document. Always consult your physician for interpretation.',
                style: TextStyle(
                    color: Theme.of(context)
                        .colorScheme
                        .onSurface
                        .withValues(alpha: 0.7)),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: FilledButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.check_circle_outline_rounded),
                  label: const Text('Close'),
                ),
              ),
            ],
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

    final defaultCat = widget.translation?.uiLabels['label_uncategorized'] ?? 'Uncategorized';
    Map<String, List<Map<String, dynamic>>> grouped = {defaultCat: []};
    for (var m in filteredMetrics) {
      String cat = defaultCat;
      for (var entry in _categories.entries) {
        if (entry.value.any((v) =>
            v.toLowerCase() == m['parameter'].toString().toLowerCase())) {
          cat = widget.translation?.uiLabels['label_cat_${entry.key.toLowerCase().replaceAll(' ', '_')}'] ?? entry.key;
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
              hintText: widget.translation?.uiLabels['label_search_parameters'] ?? AppLocalizations.of(context)!.searchParameters,
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

                    final String parameterName = m['parameter']?.toString() ?? '';
                    final String translatedName = widget.translation?.uiLabels['param_$parameterName'] ?? parameterName;

                    return LabResultRow(
                      parameter: translatedName,
                      unit: m['unit'] ?? '',
                      value: val,
                      minRange: minR,
                      maxRange: maxR,
                      flag: flag,
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
