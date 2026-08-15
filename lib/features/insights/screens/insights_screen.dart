import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:shimmer/shimmer.dart';
import 'insights_controller.dart';
import '../widgets/parameter_card.dart';
import '../../../shared/widgets/glassmorphism_card.dart';
import '../../../features/reports/models/report_model.dart';

class InsightsScreen extends StatefulWidget {
  const InsightsScreen({Key? key}) : super(key: key);

  @override
  State<InsightsScreen> createState() => _InsightsScreenState();
}

class _InsightsScreenState extends State<InsightsScreen> {
  final InsightsController _controller = InsightsController();

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onControllerChange);
  }

  @override
  void dispose() {
    _controller.removeListener(_onControllerChange);
    _controller.dispose();
    super.dispose();
  }

  void _onControllerChange() {
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Health Insights', style: TextStyle(fontWeight: FontWeight.bold)),
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ColorFilter.mode(Colors.black.withOpacity(0.01), BlendMode.srcOver),
          ),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Theme.of(context).colorScheme.background,
              Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
            ],
          ),
        ),
        child: SafeArea(
          child: CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                  child: Text(
                    "Track your progress over time",
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
                        ),
                  ),
                ),
              ),
              
              // Error State
              if (_controller.error != null)
                SliverToBoxAdapter(
                  child: Container(
                    margin: const EdgeInsets.all(16),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.errorContainer,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Column(
                      children: [
                        Text(
                          _controller.error!,
                          style: TextStyle(color: Theme.of(context).colorScheme.onErrorContainer),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        ElevatedButton(
                          onPressed: _controller.loadAvailableReports,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                ),

              // Report Selection Section
              SliverToBoxAdapter(
                child: _buildReportSelection(context),
              ),

              // Loading State for Comparison
              if (_controller.isLoading && _controller.availableReports.isNotEmpty)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Shimmer.fromColors(
                      baseColor: Colors.grey.shade300,
                      highlightColor: Colors.grey.shade100,
                      child: Column(
                        children: List.generate(3, (index) => Container(
                          height: 250,
                          margin: const EdgeInsets.only(bottom: 16),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(16),
                          ),
                        )),
                      ),
                    ),
                  ),
                ),

              // Parameter Charts Section
              if (_controller.comparisonResult != null && !_controller.isLoading)
                SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      final comp = _controller.comparisonResult!.comparisons[index];
                      return Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16.0),
                        child: ParameterCard(comparison: comp),
                      );
                    },
                    childCount: _controller.comparisonResult!.comparisons.length,
                  ),
                ),

              // Overall Summary Section
              if (_controller.comparisonResult != null && !_controller.isLoading)
                SliverToBoxAdapter(
                  child: _buildOverallSummary(context),
                ),

              const SliverPadding(padding: EdgeInsets.only(bottom: 40)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildReportSelection(BuildContext context) {
    if (_controller.isLoading && _controller.availableReports.isEmpty) {
      return const SizedBox(
        height: 120,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (_controller.availableReports.isEmpty) {
      return Padding(
        padding: const EdgeInsets.all(16.0),
        child: GlassmorphismCard(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: const [
                Icon(Icons.insert_chart_outlined, size: 48, color: Colors.grey),
                SizedBox(height: 16),
                Text(
                  'No reports available for comparison.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
          child: Text(
            'Select Reports (Max 5)',
            style: Theme.of(context).textTheme.titleSmall,
          ),
        ),
        SizedBox(
          height: 120,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12.0),
            itemCount: _controller.availableReports.length,
            itemBuilder: (context, index) {
              final report = _controller.availableReports[index];
              final isSelected = _controller.selectedReportIds.contains(report.id);
              
              return GestureDetector(
                onTap: () => _controller.toggleReportSelection(report.id),
                child: Container(
                  width: 110,
                  margin: const EdgeInsets.symmetric(horizontal: 4.0, vertical: 4.0),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: isSelected ? const Color(0xFFE8183C) : Colors.transparent,
                      width: 2,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.05),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      )
                    ],
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        _getIconForType(report.reportType),
                        color: isSelected ? const Color(0xFFE8183C) : Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        DateFormat('MMM d').format(report.reportDate),
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                        textAlign: TextAlign.center,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        report.title,
                        style: const TextStyle(fontSize: 10, color: Colors.grey),
                        textAlign: TextAlign.center,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _controller.selectedReportIds.length >= 2 
                  ? _controller.compareSelected 
                  : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE8183C),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text('Compare Selected'),
            ),
          ),
        ),
      ],
    );
  }

  IconData _getIconForType(String type) {
    if (type.toLowerCase().contains('blood')) return Icons.water_drop;
    if (type.toLowerCase().contains('urine')) return Icons.science;
    if (type.toLowerCase().contains('lipid')) return Icons.favorite;
    return Icons.description;
  }

  Widget _buildOverallSummary(BuildContext context) {
    final comps = _controller.comparisonResult!.comparisons;
    final significantChanges = comps.where((c) {
      if (c.values.length < 2) return false;
      final last = c.values.last;
      return last.changeFromPrevious != null && (last.changeFromPrevious!.abs() > (c.values[c.values.length - 2].value * 0.1));
    }).toList();

    if (significantChanges.isEmpty) return const SizedBox();

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: GlassmorphismCard(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "What changed since your last report?",
                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              ...significantChanges.map((c) {
                final last = c.values.last;
                final prev = c.values[c.values.length - 2];
                final isPositiveTrend = c.trend == 'improving';
                
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12.0),
                  child: Row(
                    children: [
                      Container(
                        width: 4,
                        height: 24,
                        decoration: BoxDecoration(
                          color: isPositiveTrend ? Colors.green : Colors.red,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              c.parameter,
                              style: const TextStyle(fontWeight: FontWeight.w600),
                            ),
                            Row(
                              children: [
                                Text('${prev.value}'),
                                const SizedBox(width: 4),
                                Icon(
                                  last.value > prev.value ? Icons.arrow_upward : Icons.arrow_downward,
                                  size: 14,
                                  color: Colors.grey,
                                ),
                                const SizedBox(width: 4),
                                Text('${last.value} ${c.unit}', style: const TextStyle(fontWeight: FontWeight.bold)),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ],
          ),
        ),
      ),
    );
  }
}