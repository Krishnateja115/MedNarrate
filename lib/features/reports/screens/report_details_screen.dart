import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/routing/routes.dart';
import 'package:go_router/go_router.dart';
import '../models/report_model.dart';

/// ReportDetailsScreen — takes a report ID, fetches the latest data from the backend,
/// and lets the user navigate to analysis, timeline, and toggle favourite.
class ReportDetailsScreen extends StatefulWidget {
  final String? reportId;
  // For backward compatibility with old code that passes a ReportModel directly
  final ReportModel? report;

  const ReportDetailsScreen({super.key, this.reportId, this.report});

  @override
  State<ReportDetailsScreen> createState() => _ReportDetailsScreenState();
}

class _ReportDetailsScreenState extends State<ReportDetailsScreen> {
  ReportModel? _report;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    if (widget.report != null) {
      _report = widget.report;
      _loading = false;
    } else {
      _loadReport();
    }
  }

  Future<void> _loadReport() async {
    try {
      final r = await ApiService.instance.getReport(widget.reportId!);
      if (mounted) setState(() { _report = r; _loading = false; });
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    }
  }

  Future<void> _toggleFavourite() async {
    if (_report == null) return;
    try {
      final updated = await ApiService.instance.patchReport(
        _report!.id,
        isFavourite: !_report!.isFavourite,
      );
      if (mounted) setState(() => _report = updated);
    } on ApiException catch (e) {
      if (mounted) Helpers.showError(context, e.message);
    }
  }

  Future<void> _deleteReport() async {
    if (_report == null) return;
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete Report'),
        content: const Text('Are you sure you want to delete this report? This cannot be undone.'),
        actions: [
          TextButton(onPressed: () => context.pop(false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => context.pop(true),
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    try {
      await ApiService.instance.deleteReport(_report!.id);
      if (mounted) context.pop(true);
    } on ApiException catch (e) {
      if (mounted) Helpers.showError(context, e.message);
    }
  }

  Widget _infoTile(String title, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(color: Colors.white54, fontSize: 13)),
          const SizedBox(height: 6),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text('Report Details'),
        actions: [
          if (_report != null)
            IconButton(
              onPressed: _toggleFavourite,
              icon: Icon(
                _report!.isFavourite ? Icons.favorite : Icons.favorite_border,
                color: _report!.isFavourite ? Colors.red : Colors.white70,
              ),
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Center(
                        child: Container(
                          width: 120,
                          height: 120,
                          decoration: BoxDecoration(
                            color: Colors.red.withValues(alpha: .12),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.picture_as_pdf, size: 60, color: Colors.red),
                        ),
                      ),
                      const SizedBox(height: 30),
                      _infoTile('Report', _report!.title),
                      _infoTile('Hospital', _report!.hospital),
                      _infoTile('Report Type', Helpers.reportTypeLabel(_report!.reportType)),
                      _infoTile('File Name', _report!.fileName),
                      _infoTile('Upload Date', Formatters.formatDate(_report!.uploadedAt)),
                      _infoTile('Status', Helpers.statusLabel(_report!.reportType)),
                      const SizedBox(height: 20),
                      SizedBox(
                        width: double.infinity,
                        height: 55,
                        child: FilledButton.icon(
                          onPressed: () => Navigator.pushNamed(
                            context,
                            Routes.reportAnalysis,
                            arguments: _report!.id,
                          ),
                          icon: const Icon(Icons.auto_awesome),
                          label: const Text('AI Analysis'),
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        height: 55,
                        child: FilledButton.icon(
                          onPressed: () => Navigator.pushNamed(
                            context,
                            Routes.reportTimeline,
                            arguments: _report!.id,
                          ),
                          icon: const Icon(Icons.timeline),
                          label: const Text('View Timeline'),
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        height: 55,
                        child: FilledButton.icon(
                          style: FilledButton.styleFrom(backgroundColor: Colors.red),
                          onPressed: _deleteReport,
                          icon: const Icon(Icons.delete),
                          label: const Text('Delete Report'),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }
}