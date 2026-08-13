import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';

class InsightsScreen extends StatefulWidget {
  const InsightsScreen({super.key});

  @override
  State<InsightsScreen> createState() => _InsightsScreenState();
}

class _InsightsScreenState extends State<InsightsScreen> {
  bool _loading = true;
  String? _error;
  
  int _recentCount = 0;
  int _favouriteCount = 0;
  final List<Map<String, dynamic>> _trendHighlights = [];

  @override
  void initState() {
    super.initState();
    _loadInsights();
  }

  Future<void> _loadInsights() async {
    try {
      final reports = await ApiService.instance.listReports();
      final now = DateTime.now();
      
      _recentCount = reports.where((r) => now.difference(r.reportDate).inDays <= 30).length;
      _favouriteCount = reports.where((r) => r.isFavourite).length;

      // Find most common test names to pull trends for.
      // We will look at completed reports, fetch their analyses, and count test names.
      final Map<String, int> testCounts = {};
      
      for (final report in reports.take(5)) { // limit to 5 recent to avoid huge overhead
        try {
          final analysis = await ApiService.instance.getReportAnalysis(report.id);
          for (final lv in analysis.structuredLabValues) {
            testCounts[lv.testName] = (testCounts[lv.testName] ?? 0) + 1;
          }
        } catch (_) {
          // ignore if not analyzed yet
        }
      }

      final sortedTests = testCounts.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
      final topTests = sortedTests.take(3).map((e) => e.key).toList();

      for (final test in topTests) {
        final points = await ApiService.instance.compareReports(test, limit: 5);
        if (points.length >= 2) {
          final first = points.first;
          final last = points.last;
          final diff = last.value - first.value;
          final diffStr = diff > 0 ? '+${diff.toStringAsFixed(1)}' : diff.toStringAsFixed(1);
          _trendHighlights.add({
            'test': test,
            'change': diffStr,
            'unit': last.unit,
            'status': last.flag,
            'desc': 'Changed by $diffStr ${last.unit} over ${points.length} reports.',
          });
        }
      }

      if (mounted) setState(() => _loading = false);
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text('Health Insights', style: TextStyle(fontWeight: FontWeight.bold)),
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
                      // Overview
                      Row(
                        children: [
                          Expanded(
                            child: _StatCard(
                              title: 'Recent Reports',
                              value: _recentCount.toString(),
                              subtitle: 'Last 30 days',
                              color: Colors.blue,
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: _StatCard(
                              title: 'Favourites',
                              value: _favouriteCount.toString(),
                              subtitle: 'Saved for later',
                              color: Colors.red,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 32),

                      // Trends
                      const Text('Trend Highlights', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 16),
                      
                      if (_trendHighlights.isEmpty)
                        const Padding(
                          padding: EdgeInsets.all(20),
                          child: Text('Not enough historical data to generate trends. Upload more reports of the same type.',
                            style: TextStyle(color: Colors.white54, height: 1.5)),
                        )
                      else
                        ..._trendHighlights.map((t) => _TrendCard(
                          title: t['test'],
                          change: t['change'],
                          unit: t['unit'],
                          status: t['status'],
                          desc: t['desc'],
                        )),

                      const SizedBox(height: 32),
                      
                      // Disclaimer
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: AppColors.card,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: const Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(Icons.info_outline, color: Colors.blue),
                            SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'These insights are AI-assisted and should not replace professional medical advice. Always consult your doctor before making health decisions.',
                                style: TextStyle(color: Colors.white70, height: 1.5),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final String subtitle;
  final Color color;

  const _StatCard({required this.title, required this.value, required this.subtitle, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(color: Colors.white70, fontSize: 14)),
          const SizedBox(height: 8),
          Text(value, style: TextStyle(color: color, fontSize: 32, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(subtitle, style: const TextStyle(color: Colors.white38, fontSize: 12)),
        ],
      ),
    );
  }
}

class _TrendCard extends StatelessWidget {
  final String title;
  final String change;
  final String unit;
  final String status;
  final String desc;

  const _TrendCard({
    required this.title,
    required this.change,
    required this.unit,
    required this.status,
    required this.desc,
  });

  @override
  Widget build(BuildContext context) {
    final bool isNormal = status == 'normal';
    final Color color = isNormal ? Colors.green : (status == 'high' ? Colors.orange : Colors.red);
    final IconData icon = isNormal ? Icons.check_circle_outline : Icons.warning_amber_rounded;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 24,
            backgroundColor: color.withValues(alpha: 0.15),
            child: Icon(icon, color: color),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 4),
                Text(desc, style: const TextStyle(color: Colors.white54, fontSize: 13)),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(change, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 16)),
              Text(unit, style: const TextStyle(color: Colors.white54, fontSize: 11)),
            ],
          ),
        ],
      ),
    );
  }
}