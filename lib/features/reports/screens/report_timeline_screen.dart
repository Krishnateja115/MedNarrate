import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../models/report_model.dart';

class ReportTimelineScreen extends StatelessWidget {
  final List<ReportModel> reports;

  const ReportTimelineScreen({
    super.key,
    required this.reports,
  });

  @override
  Widget build(BuildContext context) {
    final sortedReports = List<ReportModel>.from(reports)
      ..sort(
        (a, b) =>
            b.reportDate.compareTo(a.reportDate),
      );

    return Scaffold(
      backgroundColor: AppColors.background,

      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text("Report Timeline"),
      ),

      body: sortedReports.isEmpty
          ? const Center(
              child: Text(
                "No reports available.",
                style: TextStyle(
                  color: Colors.white70,
                ),
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(20),
              itemCount: sortedReports.length,

              itemBuilder: (context, index) {
                final report = sortedReports[index];

                return Container(
                  margin:
                      const EdgeInsets.only(bottom: 18),

                  child: Row(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,

                    children: [

                      Column(
                        children: [

                          Container(
                            width: 16,
                            height: 16,

                            decoration:
                                const BoxDecoration(
                              color: Colors.blue,
                              shape: BoxShape.circle,
                            ),
                          ),

                          if (index !=
                              sortedReports.length - 1)
                            Container(
                              width: 2,
                              height: 90,
                              color: Colors.blue,
                            ),

                        ],
                      ),

                      const SizedBox(width: 20),

                      Expanded(
                        child: Container(
                          padding:
                              const EdgeInsets.all(16),

                          decoration: BoxDecoration(
                            color: AppColors.card,
                            borderRadius:
                                BorderRadius.circular(
                                    18),
                          ),

                          child: Column(
                            crossAxisAlignment:
                                CrossAxisAlignment
                                    .start,

                            children: [

                              Text(
                                report.title,
                                style:
                                    const TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  fontWeight:
                                      FontWeight.bold,
                                ),
                              ),

                              const SizedBox(
                                  height: 8),

                              Text(
                                report.hospital,
                                style:
                                    const TextStyle(
                                  color:
                                      Colors.white70,
                                ),
                              ),

                              const SizedBox(
                                  height: 8),

                              Text(
                                report.reportDate
                                    .toString(),
                                style:
                                    const TextStyle(
                                  color:
                                      Colors.white54,
                                ),
                              ),

                            ],
                          ),
                        ),
                      ),

                    ],
                  ),
                );
              },
            ),
    );
  }
}