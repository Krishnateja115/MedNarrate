import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/routing/routes.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/export_service.dart';
import '../../dashboard/screens/dashboard_screen.dart';
import '../models/report_model.dart';
import '../controllers/report_detail_controller.dart';
import '../widgets/patient_view_tab.dart';
import '../widgets/clinical_view_tab.dart';
import '../widgets/lab_results_tab.dart';
import '../widgets/ai_chat_tab.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class ReportDetailsScreen extends StatefulWidget {
  final String? reportId;
  final ReportModel? report;

  const ReportDetailsScreen({super.key, this.reportId, this.report});

  @override
  State<ReportDetailsScreen> createState() => _ReportDetailsScreenState();
}

class _ReportDetailsScreenState extends State<ReportDetailsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final ReportDetailController _controller = ReportDetailController();
  bool _exporting = false;
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _controller.init(widget.reportId ?? widget.report!.id, widget.report);
    _controller.addListener(_onStateChanged);
  }

  void _onStateChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _tabController.dispose();
    _controller.removeListener(_onStateChanged);
    _controller.dispose();
    super.dispose();
  }

  Future<void> _handleDelete() async {
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

    try {
      final reportIdToDelete = _controller.report?.id ?? widget.reportId;
      if (reportIdToDelete != null) {
        await ApiService.instance.deleteReport(reportIdToDelete);
      }
      if (mounted) {
        messenger.showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(context)!.reportDeleted),
            backgroundColor: const Color(0xFF00C48C),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
        DashboardScreen.onRefreshRequested?.call();
        context.go(Routes.dashboard);
      }
    } on ApiException catch (e) {
      if (e.statusCode == 404) {
        if (mounted) {
          messenger.showSnackBar(
            SnackBar(
              content: Text(AppLocalizations.of(context)!.reportDeleted),
              backgroundColor: const Color(0xFF00C48C),
              behavior: SnackBarBehavior.floating,
            ),
          );
          DashboardScreen.onRefreshRequested?.call();
          context.go(Routes.dashboard);
        }
      } else {
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
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      resizeToAvoidBottomInset: true,
      appBar: AppBar(
        backgroundColor: theme.scaffoldBackgroundColor,
        elevation: 0,
        leadingWidth: 140,
        leading: TextButton.icon(
          onPressed: () {
            if (context.canPop()) {
              context.pop();
            } else {
              DashboardScreen.onRefreshRequested?.call();
              context.go(Routes.dashboard);
            }
          },
          icon: const Icon(Icons.arrow_back_rounded, size: 18),
          label: const Text(
            'Back',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          ),
        ),
        title: Text(AppLocalizations.of(context)!.reportDetails),
        actions: [
          if (_controller.report != null) ...[
            IconButton(
              onPressed: _controller.toggleFavourite,
              icon: Icon(
                _controller.report!.isFavourite ? Icons.favorite_rounded : Icons.favorite_border_rounded,
                color: _controller.report!.isFavourite ? Colors.redAccent : theme.colorScheme.onSurface.withValues(alpha: 0.70),
              ),
              tooltip: _controller.report!.isFavourite ? 'Unfavourite' : 'Favourite',
            ),
            Theme(
              data: theme.copyWith(
                cardColor: isDark ? const Color(0xFF1E293B) : Colors.white,
              ),
              child: PopupMenuButton<String>(
                color: isDark ? const Color(0xFF1E293B) : Colors.white,
                surfaceTintColor: Colors.transparent,
                elevation: 8,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                icon: Icon(
                  Icons.more_vert_rounded,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.70),
                ),
                onSelected: (value) async {
                  if (value == 'delete') {
                    _handleDelete();
                  } else if (value == 'export_pdf') {
                    final analysis = _controller.analysis;
                    final report = _controller.report;
                    if (analysis == null || report == null) return;
                    setState(() => _exporting = true);
                    final messenger = ScaffoldMessenger.of(context);
                    try {
                      await ExportService.instance.shareSummaryPdf(
                        analysis: analysis,
                        reportTitle: report.title,
                        reportDate: report.reportDate.toLocal().toString().split(' ').first,
                      );
                    } catch (e) {
                      messenger.showSnackBar(SnackBar(content: Text('Export failed: $e'), backgroundColor: Colors.red));
                    } finally {
                      if (mounted) setState(() => _exporting = false);
                    }
                  } else if (value == 'print') {
                    final analysis = _controller.analysis;
                    final report = _controller.report;
                    if (analysis == null || report == null) return;
                    await ExportService.instance.printSummary(
                      analysis: analysis,
                      reportTitle: report.title,
                      reportDate: report.reportDate.toLocal().toString().split(' ').first,
                    );
                  }
                },
                itemBuilder: (_) => [
                  if (_controller.analysis != null) ...[
                    PopupMenuItem(
                      value: 'export_pdf',
                      child: Row(
                        children: [
                          Icon(Icons.picture_as_pdf_outlined,
                              size: 20, color: theme.colorScheme.onSurface.withValues(alpha: 0.85)),
                          const SizedBox(width: 12),
                          Text(
                            _exporting ? 'Exporting…' : 'Export PDF',
                            style: TextStyle(color: theme.colorScheme.onSurface, fontSize: 14, fontWeight: FontWeight.w500),
                          ),
                        ],
                      ),
                    ),
                    PopupMenuItem(
                      value: 'print',
                      child: Row(
                        children: [
                          Icon(Icons.print_outlined,
                              size: 20, color: theme.colorScheme.onSurface.withValues(alpha: 0.85)),
                          const SizedBox(width: 12),
                          Text(
                            'Print / Preview',
                            style: TextStyle(color: theme.colorScheme.onSurface, fontSize: 14, fontWeight: FontWeight.w500),
                          ),
                        ],
                      ),
                    ),
                  ],
                  PopupMenuItem(
                    value: 'delete',
                    child: Row(
                      children: [
                        const Icon(Icons.delete_outline_rounded, color: Colors.redAccent, size: 20),
                        const SizedBox(width: 12),
                        Text(
                          AppLocalizations.of(context)!.deleteReport,
                          style: const TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w600, fontSize: 14),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
        bottom: _controller.report == null ? null : TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          unselectedLabelColor: theme.colorScheme.onSurface.withValues(alpha: 0.5),
          indicatorColor: AppColors.primary,
          indicatorWeight: 3,
          isScrollable: true,
          tabs: const [
            Tab(text: "For You"),
            Tab(text: "Clinical View"),
            Tab(text: "Lab Results"),
            Tab(text: "AI Chat"),
          ],
        ),
      ),
      body: _controller.isLoading
          ? const Center(child: CircularProgressIndicator())
          : _controller.error != null
              ? _buildNotFoundState(context)
              : TabBarView(
                  controller: _tabController,
                  children: [
                    PatientViewTab(
                      key: const PageStorageKey('patient_view_tab'),
                      report: _controller.report!,
                      analysis: _controller.analysis,
                    ),
                    ClinicalViewTab(
                      key: const PageStorageKey('clinical_view_tab'),
                      report: _controller.report!,
                      analysis: _controller.analysis,
                      comparison: _controller.comparison,
                    ),
                    LabResultsTab(
                      key: const PageStorageKey('lab_results_tab'),
                      report: _controller.report!,
                    ),
                    AIChatTab(
                      key: const PageStorageKey('ai_chat_tab'),
                      reportId: _controller.report!.id,
                    ),
                  ],
                ),
    );
  }

  Widget _buildNotFoundState(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.05),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.article_outlined,
                size: 64,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.38),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'Report no longer available',
              style: TextStyle(
                color: theme.colorScheme.onSurface,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 10),
            Text(
              'This report may have been deleted or is no longer accessible.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.54),
                fontSize: 14,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 32),
            FilledButton.icon(
              style: FilledButton.styleFrom(
                backgroundColor: theme.colorScheme.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              onPressed: () {
                if (context.canPop()) {
                  context.pop();
                } else {
                  context.go(Routes.reports);
                }
              },
              icon: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 20),
              label: const Text(
                'Back to Reports',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
              ),
            ),
          ],
        ),
      ),
    );
  }
}