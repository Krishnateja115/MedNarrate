import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

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

  void _handleShare(BuildContext context) {
    if (onShare != null) {
      onShare!();
    } else {
      final text = 'MedNarrate Medical Report: ${report.title}\nHospital: ${report.hospital}\nDate: ${report.reportDate.toLocal().toString().split(" ").first}\nType: ${report.reportType}';
      Share.share(text);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sharing report details...')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark ? Colors.white.withValues(alpha: 0.1) : AppColors.border,
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: isDark ? 0.3 : 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: theme.colorScheme.primary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(
            Icons.article_outlined,
            color: theme.colorScheme.primary,
            size: 24,
          ),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                report.title,
                style: TextStyle(
                  color: theme.colorScheme.onSurface,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (report.processingStatus == 'processing')
              Container(
                margin: const EdgeInsets.only(left: 8),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.blue.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.blue.withValues(alpha: 0.4)),
                ),
                child: Text(
                  AppLocalizations.of(context)!.processing,
                  style: const TextStyle(
                    color: Colors.blue,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
          ],
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Row(
            children: [
              Flexible(
                child: Text(
                  report.hospital,
                  style: TextStyle(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.60),
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                "•",
                style: TextStyle(color: theme.colorScheme.onSurface.withValues(alpha: 0.40)),
              ),
              const SizedBox(width: 6),
              Text(
                report.reportDate.toLocal().toString().split(" ").first,
                style: TextStyle(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.50),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),
        trailing: Theme(
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
              color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
              size: 22,
            ),
            onSelected: (value) {
              switch (value) {
                case "analyze":
                  onAnalyze?.call();
                  break;
                case "share":
                  _handleShare(context);
                  break;
                case "delete":
                  onDelete?.call();
                  break;
              }
            },
            itemBuilder: (context) => [
              PopupMenuItem<String>(
                value: "analyze",
                child: Row(
                  children: [
                    Icon(
                      Icons.analytics_outlined,
                      size: 20,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.85),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      "Analyze",
                      style: TextStyle(
                        color: theme.colorScheme.onSurface,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
              PopupMenuItem<String>(
                value: "share",
                child: Row(
                  children: [
                    Icon(
                      Icons.share_outlined,
                      size: 20,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.85),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      "Share",
                      style: TextStyle(
                        color: theme.colorScheme.onSurface,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
              const PopupMenuDivider(height: 1),
              PopupMenuItem<String>(
                value: "delete",
                child: Row(
                  children: [
                    const Icon(
                      Icons.delete_outline_rounded,
                      size: 20,
                      color: Colors.redAccent,
                    ),
                    const SizedBox(width: 12),
                    Text(
                      AppLocalizations.of(context)!.delete,
                      style: const TextStyle(
                        color: Colors.redAccent,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}