import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../models/report_model.dart';
import '../services/report_service.dart';
import '../widgets/report_card.dart';
import 'report_details_screen.dart';
import 'upload_screen.dart';

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  final ReportService reportService = ReportService.instance;

  final TextEditingController searchController =
      TextEditingController();

  List<ReportModel> reports = [];
  List<ReportModel> filteredReports = [];

  @override
  void initState() {
    super.initState();
    loadReports();

    searchController.addListener(() {
      final query =
          searchController.text.toLowerCase();

      setState(() {
        filteredReports = reports.where((report) {
          return report.title
                  .toLowerCase()
                  .contains(query) ||
              report.hospital
                  .toLowerCase()
                  .contains(query);
        }).toList();
      });
    });
  }

  void loadReports() {
    reports = reportService.getReports();
    filteredReports = List.from(reports);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,

      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text(
          "Medical Reports",
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      floatingActionButton:
          FloatingActionButton.extended(
        backgroundColor: AppColors.primary,

        onPressed: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) =>
                  const UploadScreen(),
            ),
          );

          if (result == true) {
            setState(() {
              loadReports();
            });
          }
        },

        icon: const Icon(Icons.upload_file),
        label: const Text("Upload"),
      ),

      body: Padding(
        padding: const EdgeInsets.all(20),

        child: Column(
          children: [

            TextField(
              controller: searchController,

              decoration: InputDecoration(
                hintText: "Search reports",

                prefixIcon:
                    const Icon(Icons.search),

                filled: true,

                fillColor: AppColors.card,

                border: OutlineInputBorder(
                  borderRadius:
                      BorderRadius.circular(18),
                  borderSide: BorderSide.none,
                ),
              ),
            ),

            const SizedBox(height: 20),

            Expanded(
              child: filteredReports.isEmpty
                  ? const Center(
                      child: Text(
                        "No Reports Uploaded",
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 18,
                        ),
                      ),
                    )
                  : ListView.builder(
                      itemCount:
                          filteredReports.length,

                      itemBuilder:
                          (context, index) {
                        final report =
                            filteredReports[index];

                        return ReportCard(
                          report: report,

                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) =>
                                    ReportDetailsScreen(
                                  report: report,
                                ),
                              ),
                            );
                          },

                          onDelete: () {
                            setState(() {
                              reportService
                                  .deleteReport(
                                      report.id);

                              loadReports();
                            });
                          },

                          onAnalyze: () {},

                          onShare: () {},
                        );
                      },
                    ),
            ),

          ],
        ),
      ),
    );
  }
}