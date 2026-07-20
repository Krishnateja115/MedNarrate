import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../models/report_model.dart';
import 'report_analysis_screen.dart';

class ReportDetailsScreen extends StatelessWidget {
  final ReportModel report;

  const ReportDetailsScreen({
    super.key,
    required this.report,
  });

  Widget infoTile(
    String title,
    String value,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 18),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [

          Text(
            title,
            style: const TextStyle(
              color: Colors.white54,
              fontSize: 13,
            ),
          ),

          const SizedBox(height: 6),

          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 17,
              fontWeight: FontWeight.w600,
            ),
          ),

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
        title: const Text(
          "Report Details",
        ),
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(22),

        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,

          children: [

            Center(
              child: Container(
                width: 120,
                height: 120,

                decoration: BoxDecoration(
                  color: Colors.red.withValues(
                    alpha: .12,
                  ),
                  shape: BoxShape.circle,
                ),

                child: const Icon(
                  Icons.picture_as_pdf,
                  size: 60,
                  color: Colors.red,
                ),
              ),
            ),

            const SizedBox(height: 30),

            infoTile(
              "Report",
              report.title,
            ),

            infoTile(
              "Hospital",
              report.hospital,
            ),

            infoTile(
              "Report Type",
              report.reportType,
            ),

            infoTile(
              "File Name",
              report.fileName,
            ),

            infoTile(
              "Upload Date",
              report.uploadedAt
                  .toString()
                  .split(".")
                  .first,
            ),

            const SizedBox(height: 20),

            SizedBox(
              width: double.infinity,
              height: 55,

              child: FilledButton.icon(
                onPressed: () {},

                icon: const Icon(
                  Icons.picture_as_pdf,
                ),

                label: const Text(
                  "Open PDF",
                ),
              ),
            ),

            const SizedBox(height: 16),

            SizedBox(
              width: double.infinity,
              height: 55,

              child: FilledButton.icon(
                onPressed: () {

                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) =>
                          ReportAnalysisScreen(
                        report: report,
                      ),
                    ),
                  );

                },

                icon: const Icon(
                  Icons.auto_awesome,
                ),

                label: const Text(
                  "Analyze with AI",
                ),
              ),
            ),

            const SizedBox(height: 16),

            SizedBox(
              width: double.infinity,
              height: 55,

              child: FilledButton.icon(
                onPressed: () {},

                icon: const Icon(
                  Icons.share,
                ),

                label: const Text(
                  "Share Report",
                ),
              ),
            ),

            const SizedBox(height: 16),

            SizedBox(
              width: double.infinity,
              height: 55,

              child: FilledButton.icon(
                style: FilledButton.styleFrom(
                  backgroundColor: Colors.red,
                ),

                onPressed: () {},

                icon: const Icon(
                  Icons.delete,
                ),

                label: const Text(
                  "Delete Report",
                ),
              ),
            ),

          ],
        ),
      ),
    );
  }
}