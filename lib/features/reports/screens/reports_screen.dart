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
import '../../../core/services/report_polling_service.dart';
import 'dart:async';

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
  
  final Map<String, StreamSubscription> _pollingSubscriptions = {};

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
      if (mounted) {
        setState(() { _reports = reports; _loading = false; });
        _startPollingForProcessingReports();
      }
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    }
  }

  void _startPollingForProcessingReports() {
    for (var report in _reports) {
      if (report.processingStatus == 'processing' && !_pollingSubscriptions.containsKey(report.id)) {
        _pollingSubscriptions[report.id] = ReportPollingService.instance.pollReportStatus(report.id).listen((status) {
          if (status == ReportStatus.completed || status == ReportStatus.failed) {
            _pollingSubscriptions[report.id]?.cancel();
            _pollingSubscriptions.remove(report.id);
            _loadReports(); // Reload to get updated data
          }
        });
      }
    }
  }

  @override
  void dispose() {
    for (var sub in _pollingSubscriptions.values) {
      sub.cancel();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text('Reports'),
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Colors.white,
        elevation: 4,
        onPressed: () async {
          await context.push(Routes.upload);
          _loadReports();
        },
        child: Icon(Icons.add_rounded, size: 28),
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
          SizedBox(height: 8),
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
                            Text(_error!, style: TextStyle(color: Colors.redAccent)),
                            SizedBox(height: 16),
                            TextButton.icon(
                              onPressed: _loadReports,
                              icon: Icon(Icons.refresh, color: Theme.of(context).colorScheme.onSurface),
                              label: Text('Retry', style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
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
                                SizedBox(height: 20),
                                Text('No reports found',
                                    style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 20, fontWeight: FontWeight.bold)),
                                SizedBox(height: 8),
                                Text('Upload your first medical report to get started',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 14)),
                                SizedBox(height: 24),
                                FilledButton.icon(
                                  style: FilledButton.styleFrom(
                                    backgroundColor: Theme.of(context).colorScheme.primary,
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                                  ),
                                  onPressed: () async {
                                    await context.push(Routes.upload);
                                    _loadReports();
                                  },
                                  icon: Icon(Icons.upload_file_rounded, color: Colors.white),
                                  label: Text(
                                    'Upload your first report',
                                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                                  ),
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
        selectedColor: Theme.of(context).colorScheme.primary,
        backgroundColor: Theme.of(context).cardColor,
        checkmarkColor: Colors.white,
        side: BorderSide(
          color: selected ? Theme.of(context).colorScheme.primary : AppColors.border,
          width: 1,
        ),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        labelStyle: TextStyle(
          color: selected ? Colors.white : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70),
          fontWeight: selected ? FontWeight.bold : FontWeight.w500,
          fontSize: 13,
        ),
        onSelected: (_) => onTap(),
      ),
    );
  }
}