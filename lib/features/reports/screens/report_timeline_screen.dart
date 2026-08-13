import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/api_models.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/utils/formatters.dart';

class ReportTimelineScreen extends StatefulWidget {
  final String reportId;

  const ReportTimelineScreen({super.key, required this.reportId});

  @override
  State<ReportTimelineScreen> createState() => _ReportTimelineScreenState();
}

class _ReportTimelineScreenState extends State<ReportTimelineScreen> {
  List<ComparePoint>? _points;
  ComparePreviousResult? _comparison;
  bool _loading = true;
  String? _error;
  String _selectedTest = '';
  List<String> _availableTests = [];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      // Get analysis to find test names
      final analysis = await ApiService.instance.getReportAnalysis(widget.reportId);
      final testNames = analysis.structuredLabValues.map((v) => v.testName).toList();
      // Try to get comparison
      final comparison = await ApiService.instance.comparePrevious(widget.reportId);
      if (mounted) {
        setState(() {
          _comparison = comparison;
          _availableTests = testNames;
          _selectedTest = testNames.isNotEmpty ? testNames.first : '';
          _loading = false;
        });
      }
      if (_selectedTest.isNotEmpty) {
        await _loadPoints(_selectedTest);
      }
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    }
  }

  Future<void> _loadPoints(String testName) async {
    try {
      final points = await ApiService.instance.compareReports(testName);
      if (mounted) setState(() => _points = points);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text('Timeline'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Comparison card
                      if (_comparison != null) ...[
                        if (_comparison!.comparable && _comparison!.narrativeSummary != null)
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: AppColors.card,
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Compared to Previous Report',
                                    style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                                const SizedBox(height: 8),
                                Text(_comparison!.narrativeSummary!,
                                    style: const TextStyle(color: Colors.white70, height: 1.5)),
                              ],
                            ),
                          )
                        else
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: AppColors.card,
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: const Text('No earlier report available for comparison.',
                                style: TextStyle(color: Colors.white54)),
                          ),
                        const SizedBox(height: 24),
                      ],

                      // Test selector
                      if (_availableTests.isNotEmpty) ...[
                        const Text('Test Trend',
                            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                        const SizedBox(height: 12),
                        DropdownButton<String>(
                          value: _selectedTest,
                          dropdownColor: AppColors.card,
                          style: const TextStyle(color: Colors.white),
                          underline: const SizedBox.shrink(),
                          onChanged: (v) {
                            setState(() { _selectedTest = v!; _points = null; });
                            _loadPoints(v!);
                          },
                          items: _availableTests.map((t) => DropdownMenuItem(
                            value: t,
                            child: Text(t, style: const TextStyle(color: Colors.white)),
                          )).toList(),
                        ),
                        const SizedBox(height: 16),
                        if (_points == null)
                          const Center(child: CircularProgressIndicator())
                        else if (_points!.isEmpty)
                          const Text('No historical data for this test.',
                              style: TextStyle(color: Colors.white54))
                        else
                          Container(
                            height: 220,
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: AppColors.card,
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: LineChart(
                              LineChartData(
                                gridData: const FlGridData(show: false),
                                titlesData: FlTitlesData(
                                  bottomTitles: AxisTitles(
                                    sideTitles: SideTitles(
                                      showTitles: true,
                                      getTitlesWidget: (value, meta) {
                                        final idx = value.toInt();
                                        if (idx < 0 || idx >= _points!.length) return const SizedBox();
                                        return Text(
                                          Formatters.formatMonthYear(_points![idx].reportDate),
                                          style: const TextStyle(color: Colors.white54, fontSize: 9),
                                        );
                                      },
                                    ),
                                  ),
                                  leftTitles: AxisTitles(
                                    sideTitles: SideTitles(showTitles: true,
                                      getTitlesWidget: (value, meta) => Text(
                                        value.toStringAsFixed(1),
                                        style: const TextStyle(color: Colors.white54, fontSize: 10),
                                      ),
                                    ),
                                  ),
                                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                                ),
                                borderData: FlBorderData(show: false),
                                lineBarsData: [
                                  LineChartBarData(
                                    spots: _points!.asMap().entries
                                        .map((e) => FlSpot(e.key.toDouble(), e.value.value))
                                        .toList(),
                                    isCurved: true,
                                    color: Colors.blue,
                                    barWidth: 3,
                                    dotData: FlDotData(
                                      getDotPainter: (spot, percent, bar, idx) =>
                                        FlDotCirclePainter(
                                          radius: 5,
                                          color: Helpers.flagColor(_points![idx].flag),
                                          strokeWidth: 2,
                                          strokeColor: Colors.white,
                                        ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                      ],
                    ],
                  ),
                ),
    );
  }
}