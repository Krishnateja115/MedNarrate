import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../models/report_model.dart';

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
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border, width: 1),
      ),
      child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Icon(Icons.article_outlined, color: Colors.white),
        ),
        title: Text(
          report.title,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Row(
            children: [
              Text(
                report.hospital,
                style: const TextStyle(color: Colors.white54, fontSize: 13),
              ),
              const SizedBox(width: 8),
              const Text("•", style: TextStyle(color: Colors.white38)),
              const SizedBox(width: 8),
              Text(
                report.reportDate.toLocal().toString().split(" ").first,
                style: const TextStyle(color: Colors.white38, fontSize: 13),
              ),
            ],
          ),
        ),
        trailing: PopupMenuButton<String>(
          color: AppColors.surface,
          icon: const Icon(Icons.more_vert, color: Colors.white54),
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
            const PopupMenuItem(
              value: "analyze",
              child: Text("Analyze", style: TextStyle(color: Colors.white)),
            ),
            const PopupMenuItem(
              value: "share",
              child: Text("Share", style: TextStyle(color: Colors.white)),
            ),
            const PopupMenuItem(
              value: "delete",
              child: Text("Delete", style: TextStyle(color: AppColors.error)),
            ),
          ],
        ),
      ),
    );
  }
}