import 'package:flutter/material.dart';
import '../../reports/models/report_model.dart';
import 'lab_result_row.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/utils/helpers.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class LabResultsTab extends StatefulWidget {
  final ReportModel report;

  const LabResultsTab({super.key, required this.report});

  @override
  State<LabResultsTab> createState() => _LabResultsTabState();
}

class _LabResultsTabState extends State<LabResultsTab> {
  String _searchQuery = '';
  
  final Map<String, List<String>> _categories = {
    'CBC': ['Hemoglobin', 'WBC', 'RBC', 'Platelets', 'Hematocrit'],
    'Lipid Panel': ['Total Cholesterol', 'LDL Cholesterol', 'HDL Cholesterol', 'Triglycerides'],
    'Liver Function': ['ALT', 'AST', 'ALP', 'Bilirubin'],
    'Kidney Function': ['Creatinine', 'BUN', 'eGFR'],
    'Vitamins & Minerals': ['Vitamin D', 'Vitamin B12', 'Iron', 'Calcium', 'Potassium'],
  };

  void _showParameterDetails(BuildContext context, Map<String, dynamic> metric) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) {
        return Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(metric['parameter'], style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text('What is ${metric['parameter']}?', style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.w600)),
              const SizedBox(height: 4),
              Text(
                'This measures ${metric['parameter']} in your medical document. Always consult your physician for interpretation.',
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7)),
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
    List<Map<String, dynamic>> filteredMetrics = widget.report.metrics.where((m) {
      final paramName = m['parameter'].toString();
      if (Helpers.isMetadataParameter(paramName)) {
        return false;
      }
      return paramName.toLowerCase().contains(_searchQuery.toLowerCase());
    }).toList();

    Map<String, List<Map<String, dynamic>>> grouped = {'Uncategorized': []};
    for (var m in filteredMetrics) {
      String cat = 'Uncategorized';
      for (var entry in _categories.entries) {
        if (entry.value.any((v) => v.toLowerCase() == m['parameter'].toString().toLowerCase())) {
          cat = entry.key;
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
              hintText: AppLocalizations.of(context)!.searchParameters,
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
                    child: Text(cat, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.primary)),
                  ),
                  ...items.map((m) {
                    final double val = (m['value'] is num) ? (m['value'] as num).toDouble() : 0.0;
                    final double? minR = (m['min_range'] is num) ? (m['min_range'] as num).toDouble() : ((m['ref_low'] is num) ? (m['ref_low'] as num).toDouble() : null);
                    final double? maxR = (m['max_range'] is num) ? (m['max_range'] as num).toDouble() : ((m['ref_high'] is num) ? (m['ref_high'] as num).toDouble() : null);
                    final String flag = m['flag']?.toString() ?? 'not_classified';

                    return LabResultRow(
                      parameter: m['parameter'],
                      unit: m['unit'] ?? '',
                      value: val,
                      minRange: minR,
                      maxRange: maxR,
                      flag: flag,
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
