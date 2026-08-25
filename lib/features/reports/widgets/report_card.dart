import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../models/report_model.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class ReportCard extends StatelessWidget {
  final ReportModel report;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;
  final VoidCallback? onShare;
  final VoidCallback? onAnalyze;

  const ReportCard({
    super.key,
    required this.report,
    this.onTap,
    this.onDelete,
    this.onShare,
    this.onAnalyze,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border, width: 1),
      ),
      child: ListTile(
        onTap: onTap,
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          padding: EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(Icons.article_outlined, color: Theme.of(context).colorScheme.onSurface),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                report.title,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurface,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ),
            if (report.processingStatus == 'processing')
              Container(
                margin: const EdgeInsets.only(left: 8),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.blue.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.blue.withValues(alpha: 0.5)),
                ),
                child: Text(AppLocalizations.of(context)!.processing, style: TextStyle(color: Colors.blue, fontSize: 10, fontWeight: FontWeight.bold)),
              ),
          ],
        ),
        subtitle: Padding(
          padding: EdgeInsets.only(top: 6),
          child: Row(
            children: [
              Text(
                report.hospital,
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 13),
              ),
              SizedBox(width: 8),
              Text("•", style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.38))),
              SizedBox(width: 8),
              Text(
                report.reportDate.toLocal().toString().split(" ").first,
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.38), fontSize: 13),
              ),
            ],
          ),
        ),
        trailing: PopupMenuButton<String>(
          color: AppColors.surface,
          icon: Icon(Icons.more_vert, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)),
          onSelected: (value) {
            switch (value) {
              case "analyze":
                onAnalyze?.call();
                break;
              case "share":
                onShare?.call();
                break;
              case "delete":
                onDelete?.call();
                break;
            }
          },
          itemBuilder: (context) => [
            PopupMenuItem(
              value: "analyze",
              child: Text("Analyze", style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
            ),
            PopupMenuItem(
              value: "share",
              child: Text("Share", style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
            ),
            PopupMenuItem(
              value: "delete",
              child: Text(AppLocalizations.of(context)!.delete, style: TextStyle(color: AppColors.error)),
            ),
          ],
        ),
      ),
    );
  }
}