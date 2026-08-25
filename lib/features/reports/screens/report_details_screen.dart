import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../models/report_model.dart';
import '../controllers/report_detail_controller.dart';
import '../widgets/summary_tab.dart';
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
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
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


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      resizeToAvoidBottomInset: true,
      appBar: AppBar(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
        title: Text(AppLocalizations.of(context)!.reportDetails),
        actions: [
          if (_controller.report != null) ...[  
            IconButton(
              onPressed: _controller.toggleFavourite,
              icon: Icon(
                _controller.report!.isFavourite ? Icons.favorite : Icons.favorite_border,
                color: _controller.report!.isFavourite ? Colors.red : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70),
              ),
              tooltip: _controller.report!.isFavourite ? 'Unfavourite' : 'Favourite',
            ),
            PopupMenuButton<String>(
              onSelected: (value) async {
                if (value == 'delete') {
                  // Capture before async gap
                  final messenger = ScaffoldMessenger.of(context);
                  final router = GoRouter.of(context);
                  final confirm = await showDialog<bool>(
                    context: context,
                    builder: (_) => AlertDialog(
                      title: Text(AppLocalizations.of(context)!.deleteReportTitle),
                      content: Text(AppLocalizations.of(context)!.deleteReportConfirm),
                      actions: [
                        TextButton(onPressed: () => router.pop(), child: Text(AppLocalizations.of(context)!.cancel)),
                        TextButton(
                          onPressed: () => Navigator.of(context).pop(true),
                          child: Text(AppLocalizations.of(context)!.delete, style: TextStyle(color: Colors.red)),
                        ),
                      ],
                    ),
                  );
                  if (confirm != true || !mounted) return;
                  try {
                    await ApiService.instance.deleteReport(_controller.report!.id);
                    if (mounted) {
                      messenger.showSnackBar(SnackBar(
                        content: Text(AppLocalizations.of(context)!.reportDeleted),
                        backgroundColor: Color(0xFF00C48C),
                      ));
                      router.pop();
                    }
                  } catch (e) {
                    if (mounted) {
                      messenger.showSnackBar(SnackBar(
                        content: Text('Delete failed: $e'),
                        backgroundColor: Colors.red,
                      ));
                    }
                  }
                }
              },
              itemBuilder: (_) => [
                PopupMenuItem(
                  value: 'delete',
                  child: Row(
                    children: [
                      const Icon(Icons.delete_outline, color: Colors.red),
                      const SizedBox(width: 12),
                      Text(AppLocalizations.of(context)!.deleteReport, style: const TextStyle(color: Colors.red)),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          unselectedLabelColor: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          indicatorColor: AppColors.primary,
          indicatorWeight: 3,
          tabs: [
            Tab(text: AppLocalizations.of(context)!.summary),
            Tab(text: AppLocalizations.of(context)!.labResultsTab),
            Tab(text: AppLocalizations.of(context)!.aiChatTab),
          ],
        ),
      ),
      body: _controller.isLoading
          ? Center(child: CircularProgressIndicator())
          : _controller.error != null
              ? Center(child: Text(_controller.error!, style: TextStyle(color: Colors.red)))
              : TabBarView(
                  controller: _tabController,
                  children: [
                    SummaryTab(
                      key: const PageStorageKey('summary_tab'),
                      report: _controller.report!,
                      isProfessionalMode: _controller.professionalMode,
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
}