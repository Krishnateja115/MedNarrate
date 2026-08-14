import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/routing/routes.dart';
import '../models/report_model.dart';
import '../widgets/report_card.dart';
import '../../../shared/widgets/skeleton_loader.dart';
import '../../../shared/widgets/illustrations.dart';
import 'package:go_router/go_router.dart';
import '../widgets/search_bar.dart';

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  List<ReportModel> _reports = [];
  bool _loading = true;
  String? _error;
  String? _searchQuery;
  String? _filterType;
  bool? _filterFavourite;

  @override
  void initState() {
    super.initState();
    _loadReports();
  }

  Future<void> _loadReports() async {
    setState(() { _loading = true; _error = null; });
    try {
      final reports = await ApiService.instance.listReports(
        search: _searchQuery,
        reportType: _filterType,
        isFavourite: _filterFavourite,
      );
      if (mounted) setState(() { _reports = reports; _loading = false; });
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Reports'),
        backgroundColor: AppColors.background,
        elevation: 0,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          await context.push(Routes.upload);
          _loadReports();
        },
        child: const Icon(Icons.add),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: ReportSearchBar(
              onChanged: (q) {
                _searchQuery = q.isEmpty ? null : q;
                _loadReports();
              },
            ),
          ),
          // Filter chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                _filterChip('All', _filterType == null && _filterFavourite == null, () {
                  setState(() { _filterType = null; _filterFavourite = null; });
                  _loadReports();
                }),
                _filterChip('Favourites', _filterFavourite == true, () {
                  setState(() { _filterFavourite = _filterFavourite == true ? null : true; _filterType = null; });
                  _loadReports();
                }),
                ...['blood', 'pathology', 'health', 'other'].map((t) =>
                  _filterChip(Helpers.reportTypeLabel(t), _filterType == t, () {
                    setState(() { _filterType = _filterType == t ? null : t; _filterFavourite = null; });
                    _loadReports();
                  }),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: _loading
                ? ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: 5,
                    itemBuilder: (context, index) => const SkeletonReportCard(),
                  )
                : _error != null
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(_error!, style: const TextStyle(color: Colors.red)),
                            const SizedBox(height: 16),
                            TextButton.icon(
                              onPressed: _loadReports,
                              icon: const Icon(Icons.refresh),
                              label: const Text('Retry'),
                            ),
                          ],
                        ),
                      )
                    : _reports.isEmpty
                        ? Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const EmptyHistoryIllustration(),
                                const SizedBox(height: 20),
                                const Text('No reports found',
                                    style: TextStyle(color: Colors.white70, fontSize: 18, fontWeight: FontWeight.w600)),
                                const SizedBox(height: 8),
                                const Text('Upload your first medical report to get started',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(color: Colors.white54, fontSize: 14)),
                                const SizedBox(height: 20),
                                FilledButton.icon(
                                  onPressed: () async {
                                    await context.push(Routes.upload);
                                    _loadReports();
                                  },
                                  icon: const Icon(Icons.upload_file),
                                  label: const Text('Upload your first report'),
                                ),
                              ],
                            ),
                          )
                        : RefreshIndicator(
                            onRefresh: _loadReports,
                            child: ListView.builder(
                              padding: const EdgeInsets.symmetric(horizontal: 16),
                              itemCount: _reports.length,
                              itemBuilder: (context, index) {
                                final report = _reports[index];
                                return Padding(
                                  padding: const EdgeInsets.only(bottom: 12),
                                  child: GestureDetector(
                                    onTap: () => context.push(Routes.reportDetails, extra: report.id),
                                    child: ReportCard(report: report),
                                  ),
                                );
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(String label, bool selected, VoidCallback onTap) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label),
        selected: selected,
        onSelected: (_) => onTap(),
      ),
    );
  }
}