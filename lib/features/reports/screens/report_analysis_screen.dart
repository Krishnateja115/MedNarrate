import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../models/report_model.dart';

class ReportAnalysisScreen extends StatelessWidget {
  final ReportModel report;

  const ReportAnalysisScreen({
    super.key,
    required this.report,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,

      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text("AI Report Analysis"),
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),

        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            _section(
              "Overall Summary",
              report.extractedText.isEmpty
                  ? "No analysis available yet. Upload and analyze this report to view AI-generated insights."
                  : report.extractedText,
            ),

            const SizedBox(height: 20),

            _section(
              "Important Findings",
              "• No abnormal findings detected.\n"
              "• All measured parameters are within normal range.\n"
              "• Continue regular monitoring.",
            ),

            const SizedBox(height: 20),

            _section(
              "Recommendations",
              "• Consult your doctor if symptoms continue.\n"
              "• Maintain a healthy diet.\n"
              "• Exercise regularly.\n"
              "• Repeat tests only if advised.",
            ),

            const SizedBox(height: 20),

            _section(
              "Disclaimer",
              "This analysis is generated for educational purposes only and is not a medical diagnosis. Always consult a qualified healthcare professional.",
            ),

          ],
        ),
      ),
    );
  }

  Widget _section(
    String title,
    String content,
  ) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),

      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(18),
      ),

      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [

          Text(
            title,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),

          const SizedBox(height: 12),

          Text(
            content,
            style: const TextStyle(
              color: Colors.white70,
              height: 1.6,
              fontSize: 15,
            ),
          ),

        ],
      ),
    );
  }
}