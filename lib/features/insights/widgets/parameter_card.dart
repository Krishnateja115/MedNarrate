import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../../models/comparison_models.dart';
import '../../../shared/widgets/glassmorphism_card.dart';

class ParameterCard extends StatelessWidget {
  final ParameterComparison comparison;

  const ParameterCard({Key? key, required this.comparison}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    
    // Sort values chronologically
    final sortedValues = List<LabValuePoint>.from(comparison.values)
      ..sort((a, b) => a.date.compareTo(b.date));

    // Determine colors
    Color trendColor;
    IconData trendIcon;
    if (comparison.trend == 'improving') {
      trendColor = Colors.green;
      trendIcon = Icons.trending_up;
    } else if (comparison.trend == 'worsening') {
      trendColor = Colors.red;
      trendIcon = Icons.trending_down;
    } else {
      trendColor = Colors.amber;
      trendIcon = Icons.remove;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 24),
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header Row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    comparison.parameter,
                    style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                  ),
                ),
                Row(
                  children: [
                    Icon(trendIcon, color: trendColor, size: 20),
                    const SizedBox(width: 4),
                    Text(
                      comparison.trend.toUpperCase(),
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: trendColor,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 8),
            
            // Reference Range
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                'Normal: ${comparison.referenceRange} ${comparison.unit}',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: colorScheme.onSurfaceVariant,
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Chart
            RepaintBoundary(
              child: SizedBox(
                height: 200,
                child: sortedValues.length == 1
                    ? _buildBarChart(context, sortedValues)
                    : _buildLineChart(context, sortedValues),
              ),
            ),
            const SizedBox(height: 16),

            // AI Summary
            if (comparison.aiSummary != null && comparison.aiSummary!.isNotEmpty)
              GlassmorphismCard(
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.auto_awesome, color: Color(0xFFE8183C), size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          comparison.aiSummary!,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.textTheme.bodyMedium?.color?.withOpacity(0.85),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildLineChart(BuildContext context, List<LabValuePoint> values) {
    List<FlSpot> spots = [];
    for (int i = 0; i < values.length; i++) {
      spots.add(FlSpot(i.toDouble(), values[i].value));
    }

    double minY = values.map((e) => e.value).reduce((a, b) => a < b ? a : b);
    double maxY = values.map((e) => e.value).reduce((a, b) => a > b ? a : b);

    // Extract reference range min/max
    double? refMin, refMax;
    try {
      final parts = comparison.referenceRange.split(RegExp(r'[-–~to]+'));
      if (parts.length >= 2) {
        refMin = double.parse(parts[0].trim());
        refMax = double.parse(parts[1].trim());
        if (refMin < minY) minY = refMin;
        if (refMax > maxY) maxY = refMax;
      }
    } catch (_) {}

    // Add padding to Y axis
    final yRange = maxY - minY;
    minY = (minY - (yRange * 0.1)).clamp(0.0, double.infinity);
    maxY = maxY + (yRange * 0.1);
    if (minY == maxY) {
      minY = minY - 10;
      maxY = maxY + 10;
    }

    return LineChart(
      duration: const Duration(milliseconds: 800),
      curve: Curves.easeOutCubic,
      LineChartData(
        minY: minY,
        maxY: maxY,
        minX: -0.2,
        maxX: (values.length - 1).toDouble() + 0.2,
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          horizontalInterval: ((maxY - minY) / 4) > 0 ? (maxY - minY) / 4 : 1,
        ),
        titlesData: FlTitlesData(
          show: true,
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 30,
              getTitlesWidget: (value, meta) {
                if (value < 0 || value >= values.length) return const SizedBox();
                final intIndex = value.toInt();
                if (intIndex.toDouble() != value) return const SizedBox();
                final date = values[intIndex].date;
                return Padding(
                  padding: const EdgeInsets.only(top: 8.0),
                  child: Text(
                    DateFormat('MMM d').format(date),
                    style: const TextStyle(fontSize: 10, color: Colors.grey),
                  ),
                );
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              getTitlesWidget: (value, meta) {
                return Text(
                  value.toStringAsFixed(1),
                  style: const TextStyle(fontSize: 10, color: Colors.grey),
                );
              },
            ),
          ),
        ),
        borderData: FlBorderData(show: false),
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            // tooltipBgColor is removed, we'll configure background differently or use default
            getTooltipItems: (touchedSpots) {
              return touchedSpots.map((spot) {
                final point = values[spot.x.toInt()];
                return LineTooltipItem(
                  '${point.value} ${comparison.unit}\n${point.status.toUpperCase()}',
                  const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                );
              }).toList();
            },
          ),
        ),
        extraLinesData: ExtraLinesData(
          horizontalLines: refMin != null && refMax != null
              ? [
                  HorizontalLine(
                    y: refMax,
                    color: Colors.green.withOpacity(0.3),
                    strokeWidth: 2,
                    dashArray: [5, 5],
                  ),
                  HorizontalLine(
                    y: refMin,
                    color: Colors.green.withOpacity(0.3),
                    strokeWidth: 2,
                    dashArray: [5, 5],
                  ),
                ]
              : [],
        ),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: const Color(0xFFE8183C), // Crimson
            barWidth: 3,
            isStrokeCapRound: true,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, percent, barData, index) {
                final status = values[index].status;
                Color dotColor = Colors.green;
                if (status == 'low' || status == 'high' || status == 'critical') {
                  dotColor = Colors.red;
                } else if (status == 'borderline') {
                  dotColor = Colors.amber;
                }
                return FlDotCirclePainter(
                  radius: 5,
                  color: dotColor,
                  strokeWidth: 2,
                  strokeColor: Colors.white,
                );
              },
            ),
            belowBarData: BarAreaData(
              show: true,
              color: const Color(0xFFE8183C).withOpacity(0.1),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBarChart(BuildContext context, List<LabValuePoint> values) {
    // A single bar for when there's only 1 report
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            '${values.first.value} ${comparison.unit}',
            style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Text(
            DateFormat('MMM d, yyyy').format(values.first.date),
            style: const TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          const Text('Need at least 2 reports to show a trend graph.', 
            style: TextStyle(fontStyle: FontStyle.italic, color: Colors.grey)),
        ],
      ),
    );
  }
}
