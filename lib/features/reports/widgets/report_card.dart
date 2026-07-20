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
    return Card(
      color: AppColors.card,
      margin: const EdgeInsets.only(bottom: 16),

      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),

      child: ListTile(
        onTap: onTap,

        leading: CircleAvatar(
          backgroundColor:
              Colors.red.withValues(alpha: .15),

          child: const Icon(
            Icons.picture_as_pdf,
            color: Colors.red,
          ),
        ),

        title: Text(
          report.title,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),

        subtitle: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,

          children: [

            const SizedBox(height: 4),

            Text(
              report.hospital,
              style: const TextStyle(
                color: Colors.white60,
              ),
            ),

            const SizedBox(height: 2),

            Text(
              report.reportDate
                  .toLocal()
                  .toString()
                  .split(" ")
                  .first,
              style: const TextStyle(
                color: Colors.white38,
              ),
            ),

          ],
        ),

        trailing: PopupMenuButton<String>(
          color: AppColors.card,

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

          itemBuilder: (context) => const [

            PopupMenuItem(
              value: "analyze",
              child: Text("Analyze"),
            ),

            PopupMenuItem(
              value: "share",
              child: Text("Share"),
            ),

            PopupMenuItem(
              value: "delete",
              child: Text("Delete"),
            ),

          ],
        ),
      ),
    );
  }
}