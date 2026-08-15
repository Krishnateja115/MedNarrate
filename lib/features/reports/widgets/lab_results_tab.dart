import 'package:flutter/material.dart';
import '../../reports/models/report_model.dart';
import 'lab_result_row.dart';
import '../../../core/constants/app_colors.dart';

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
              Text(metric['parameter'], style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              SizedBox(height: 8),
              Text('What is ${metric['parameter']}?', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.w600)),
              SizedBox(height: 4),
              Text(
                'This measures the amount of ${metric['parameter']} in your blood. It is an important indicator of your overall health.',
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7)),
              ),
              SizedBox(height: 24),
              Text('Historical Trend', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              SizedBox(height: 12),
              Container(
                height: 150,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Theme.of(context).cardColor,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                ),
                child: Center(
                  child: Text(
                    'Mini-chart goes here',
                    style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.3)),
                  ),
                ),
              ),
              SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: FilledButton.icon(
                  onPressed: () {
                    Navigator.pop(context);
                    // Switch to Chat tab and pre-fill input
                    // (Requires callback to parent, handled later)
                  },
                  icon: Icon(Icons.smart_toy),
                  label: Text('Ask AI about this'),
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
      return m['parameter'].toString().toLowerCase().contains(_searchQuery.toLowerCase());
    }).toList();

    // Grouping logic (simplified)
    Map<String, List<Map<String, dynamic>>> grouped = {'Uncategorized': []};
    for (var m in filteredMetrics) {
      String cat = 'Uncategorized';
      for (var entry in _categories.entries) {
        if (entry.value.contains(m['parameter'])) {
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
              hintText: 'Search parameters...',
              prefixIcon: Icon(Icons.search),
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
              if (items.isEmpty) return SizedBox.shrink();

              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: Text(cat, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.primary)),
                  ),
                  ...items.map((m) {
                    return LabResultRow(
                      parameter: m['parameter'],
                      unit: m['unit'],
                      value: (m['value'] as num).toDouble(),
                      minRange: (m['min_range'] as num).toDouble(),
                      maxRange: (m['max_range'] as num).toDouble(),
                      onTap: () => _showParameterDetails(context, m),
                    );
                  }).toList(),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}
