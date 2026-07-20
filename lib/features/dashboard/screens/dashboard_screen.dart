import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../widgets/dashboard_header.dart';
import '../widgets/dashboard_statistics_card.dart';
import '../widgets/health_progress_card.dart';
import '../widgets/health_score_card.dart';
import '../widgets/health_tip_card.dart';
import '../widgets/medicine_reminder_card.dart';
import '../widgets/quick_action_card.dart';
import '../widgets/recent_report_card.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,

      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(22),

          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,

            children: [

              //--------------------------------------------------
              // HEADER
              //--------------------------------------------------

              const DashboardHeader(
                name: "Krishna",
              ),

              const SizedBox(height: 30),

              //--------------------------------------------------
              // HEALTH SCORE
              //--------------------------------------------------

              const HealthScoreCard(
                score: 92,
              ),

              const SizedBox(height: 30),

              //--------------------------------------------------
              // STATISTICS
              //--------------------------------------------------

              Row(
                children: [

                  DashboardStatisticsCard(
                    title: "Reports",
                    value: "12",
                    icon: Icons.description_outlined,
                    color: Colors.blue,
                  ),

                  const SizedBox(width: 12),

                  DashboardStatisticsCard(
                    title: "Medicines",
                    value: "4",
                    icon: Icons.medication_outlined,
                    color: Colors.orange,
                  ),

                  const SizedBox(width: 12),

                  DashboardStatisticsCard(
                    title: "Alerts",
                    value: "1",
                    icon: Icons.warning_amber_outlined,
                    color: Colors.red,
                  ),

                ],
              ),

              const SizedBox(height: 35),

              //--------------------------------------------------
              // QUICK ACTIONS
              //--------------------------------------------------

              const Text(
                "Quick Actions",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 20),

              Row(
                children: [

                  QuickActionCard(
                    icon: Icons.upload_file_rounded,
                    title: "Upload\nReport",
                    onTap: () {},
                  ),

                  QuickActionCard(
                    icon: Icons.smart_toy_outlined,
                    title: "AI\nAssistant",
                    onTap: () {},
                  ),

                ],
              ),

              const SizedBox(height: 15),

              Row(
                children: [

                  QuickActionCard(
                    icon: Icons.bar_chart_rounded,
                    title: "Insights",
                    onTap: () {},
                  ),

                  QuickActionCard(
                    icon: Icons.medication_rounded,
                    title: "Medicines",
                    onTap: () {},
                  ),

                ],
              ),

              const SizedBox(height: 35),

              //--------------------------------------------------
              // TODAY'S MEDICINE
              //--------------------------------------------------

              const MedicineReminderCard(),

              const SizedBox(height: 35),

              //--------------------------------------------------
              // RECENT REPORTS
              //--------------------------------------------------

              const Text(
                "Recent Reports",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 20),

              const RecentReportCard(
                title: "Complete Blood Count",
                hospital: "Apollo Hospital",
                date: "12 July 2026",
              ),

              const RecentReportCard(
                title: "Lipid Profile",
                hospital: "MedPlus Diagnostics",
                date: "03 July 2026",
              ),

              const RecentReportCard(
                title: "HbA1c Report",
                hospital: "Yashoda Hospital",
                date: "21 June 2026",
              ),

              const SizedBox(height: 35),

              //--------------------------------------------------
              // HEALTH TIP
              //--------------------------------------------------

              const HealthTipCard(),

              const SizedBox(height: 30),

              //--------------------------------------------------
              // WEEKLY PROGRESS
              //--------------------------------------------------

              const HealthProgressCard(),

              const SizedBox(height: 40),

            ],
          ),
        ),
      ),
    );
  }
}