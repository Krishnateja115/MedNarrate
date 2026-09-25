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
import 'package:mednarrate/l10n/app_localizations.dart';

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});

  static VoidCallback? onRefreshRequested;

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
  Timer? _searchDebounce;

  @override
  void initState() {
    super.initState();
    ReportsScreen.onRefreshRequested = _loadReports;
    _loadReports();
  }

  Future<void> _loadReports() async {
    if (!mounted) return;
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
            _loadReports();
          }
        });
      }
    }
  }

  Future<void> _handleDeleteReport(ReportModel report) async {
    final messenger = ScaffoldMessenger.of(context);
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: [
            const Icon(Icons.delete_outline_rounded, color: Colors.redAccent, size: 24),
            const SizedBox(width: 10),
            Text(AppLocalizations.of(context)!.deleteReportTitle),
          ],
        ),
        content: Text(AppLocalizations.of(context)!.deleteReportConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(
              AppLocalizations.of(context)!.cancel,
              style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7)),
            ),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.redAccent,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(
              AppLocalizations.of(context)!.delete,
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );

    if (confirm != true || !mounted) return;

    // Immediately update local state to feel snappy
    setState(() {
      _reports.removeWhere((r) => r.id == report.id);
    });

    try {
      await ApiService.instance.deleteReport(report.id);
      if (mounted) {
        messenger.showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(context)!.reportDeleted),
            backgroundColor: const Color(0xFF00C48C),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
      }
    } on ApiException catch (e) {
      if (e.statusCode == 404) {
        // Already deleted elsewhere, ignore error
        if (mounted) {
          messenger.showSnackBar(
            SnackBar(
              content: Text(AppLocalizations.of(context)!.reportDeleted),
              backgroundColor: const Color(0xFF00C48C),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      } else {
        // Revert local state and show error
        _loadReports();
        if (mounted) {
          messenger.showSnackBar(
            SnackBar(
              content: Text('Unable to delete report: ${e.message}'),
              backgroundColor: Colors.redAccent,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    } catch (e) {
      _loadReports();
      if (mounted) {
        messenger.showSnackBar(
          const SnackBar(
            content: Text('Unable to delete report. Please try again.'),
            backgroundColor: Colors.redAccent,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  void dispose() {
    if (ReportsScreen.onRefreshRequested == _loadReports) {
      ReportsScreen.onRefreshRequested = null;
    }
    _searchDebounce?.cancel();
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
        title: Text(AppLocalizations.of(context)!.statReports),
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
        child: const Icon(Icons.add_rounded, size: 28),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: ReportSearchBar(
              onChanged: (q) {
                _searchDebounce?.cancel();
                _searchQuery = q.isEmpty ? null : q;
                _searchDebounce = Timer(const Duration(milliseconds: 400), _loadReports);
              },
            ),
          ),
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
                            Text(_error!, style: const TextStyle(color: Colors.redAccent)),
                            const SizedBox(height: 16),
                            TextButton.icon(
                              onPressed: _loadReports,
                              icon: Icon(Icons.refresh, color: Theme.of(context).colorScheme.onSurface),
                              label: Text(AppLocalizations.of(context)!.retry, style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
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
                                Text(AppLocalizations.of(context)!.noReportsFound,
                                    style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 20, fontWeight: FontWeight.bold)),
                                const SizedBox(height: 8),
                                Text(AppLocalizations.of(context)!.uploadFirstReport,
                                    textAlign: TextAlign.center,
                                    style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 14)),
                                const SizedBox(height: 24),
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
                                  icon: const Icon(Icons.upload_file_rounded, color: Colors.white),
                                  label: const Text(
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
                                    onTap: () async {
                                      await context.push(Routes.reportDetails, extra: report.id);
                                      _loadReports();
                                    },
                                    child: ReportCard(
                                      report: report,
                                      onDelete: () => _handleDeleteReport(report),
                                      onAnalyze: () async {
                                        final messenger = ScaffoldMessenger.of(context);
                                        try {
                                          messenger.showSnackBar(
                                            const SnackBar(content: Text('Starting report analysis...')),
                                          );
                                          await ApiService.instance.processReport(report.id, force: true);
                                          _loadReports();
                                        } catch (e) {
                                          if (mounted) {
                                            messenger.showSnackBar(
                                              SnackBar(content: Text('Analysis request failed: $e'), backgroundColor: Colors.red),
                                            );
                                          }
                                        }
                                      },
                                    ),
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