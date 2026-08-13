import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/routing/routes.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/reminder_service.dart';
import '../../reports/models/report_model.dart';
import '../widgets/dashboard_header.dart';
import '../widgets/dashboard_statistics_card.dart';
import '../widgets/health_progress_card.dart';
import '../widgets/health_score_card.dart';
import '../widgets/health_tip_card.dart';
import '../widgets/medicine_reminder_card.dart';
import '../widgets/quick_action_card.dart';
import '../widgets/recent_report_card.dart';
import 'package:go_router/go_router.dart';
import '../../reports/widgets/upload_card.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  bool _loading = true;
  String _userName = 'User';
  List<ReportModel> _recentReports = [];
  int _totalReports = 0;
  int _favouriteReports = 0;
  int _activeReminders = 0;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final user = await ApiService.instance.getMe();
      final reports = await ApiService.instance.listReports();
      final reminders = await ReminderService.instance.getAll();
      
      if (mounted) {
        setState(() {
          _userName = user.fullName.split(' ').first;
          _totalReports = reports.length;
          _favouriteReports = reports.where((r) => r.isFavourite).length;
          _recentReports = reports.take(3).toList();
          _activeReminders = reminders.length;
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadData,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(22),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DashboardHeader(name: _userName),
                const SizedBox(height: 30),
                const HealthScoreCard(score: 92),
                const SizedBox(height: 30),

                // Statistics
                Row(
                  children: [
                    DashboardStatisticsCard(
                      title: 'Reports',
                      value: _totalReports.toString(),
                      icon: Icons.description_outlined,
                      color: Colors.blue,
                    ),
                    const SizedBox(width: 12),
                    DashboardStatisticsCard(
                      title: 'Reminders',
                      value: _activeReminders.toString(),
                      icon: Icons.medication_outlined,
                      color: Colors.orange,
                    ),
                    const SizedBox(width: 12),
                    DashboardStatisticsCard(
                      title: 'Favourites',
                      value: _favouriteReports.toString(),
                      icon: Icons.favorite_border,
                      color: Colors.red,
                    ),
                  ],
                ),
                const SizedBox(height: 35),

                // Quick Actions
                const Text('Quick Actions', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                const SizedBox(height: 20),
                UploadCard(onTap: () async {
                  await context.push(Routes.upload);
                  _loadData();
                }),
                const SizedBox(height: 15),
                Row(
                  children: [
                    QuickActionCard(
                      icon: Icons.description_outlined,
                      title: 'All Reports',
                      onTap: () => context.push(Routes.reports),
                    ),
                    QuickActionCard(
                      icon: Icons.smart_toy_outlined,
                      title: 'AI Chat',
                      onTap: () => context.push(Routes.aiChat),
                    ),
                    QuickActionCard(
                      icon: Icons.bar_chart_rounded,
                      title: 'Insights',
                      onTap: () => context.push(Routes.insights),
                    ),
                  ],
                ),
                const SizedBox(height: 35),

                // Reminders
                const MedicineReminderCard(),
                const SizedBox(height: 35),

                // Recent Reports
                const Text('Recent Reports', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                const SizedBox(height: 20),
                if (_loading)
                  const Center(child: CircularProgressIndicator())
                else if (_recentReports.isEmpty)
                  const Center(child: Text('No recent reports.', style: TextStyle(color: Colors.white54)))
                else
                  ..._recentReports.map((report) => GestureDetector(
                    onTap: () => context.push(Routes.reportDetails, extra: report.id),
                    child: RecentReportCard(
                      title: report.title,
                      hospital: report.hospital,
                      date: report.reportDate.toString().split(' ').first,
                    ),
                  )),
                const SizedBox(height: 35),

                const HealthTipCard(),
                const SizedBox(height: 30),
                const HealthProgressCard(),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }
}