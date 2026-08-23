import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../models/report_model.dart';
import '../controllers/report_detail_controller.dart';
import '../widgets/summary_tab.dart';
import '../widgets/lab_results_tab.dart';
import '../widgets/ai_chat_tab.dart';

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
        title: Text('Report Details'),
        actions: [
          if (_controller.report != null)
            IconButton(
              onPressed: _controller.toggleFavourite,
              icon: Icon(
                _controller.report!.isFavourite ? Icons.favorite : Icons.favorite_border,
                color: _controller.report!.isFavourite ? Colors.red : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70),
              ),
            ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          unselectedLabelColor: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          indicatorColor: AppColors.primary,
          indicatorWeight: 3,
          tabs: const [
            Tab(text: 'Summary'),
            Tab(text: 'Lab Results'),
            Tab(text: 'AI Chat'),
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