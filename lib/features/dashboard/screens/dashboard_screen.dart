import 'package:flutter/material.dart';

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
import '../../../shared/widgets/skeleton_loader.dart';
import '../../../shared/widgets/offline_banner.dart';
import 'package:go_router/go_router.dart';
import '../../reports/widgets/upload_card.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

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
  int _healthScore = 0;
  int _totalLabValues = 0;
  int _abnormalCount = 0;

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

      // Compute health score from the most recent completed report's lab values
      int totalLab = 0;
      int abnormal = 0;
      for (final r in reports.take(3)) {
        if (r.processingStatus == 'completed') {
          try {
            final analysis = await ApiService.instance.getReportAnalysis(r.id);
            totalLab += analysis.structuredLabValues.length;
            abnormal += analysis.structuredLabValues.where((v) => v.flag != 'normal').length;
            break; // only use most recent
          } catch (_) {}
        }
      }
      final score = totalLab > 0 ? (((totalLab - abnormal) / totalLab) * 100).round() : 0;

      if (mounted) {
        setState(() {
          _userName = user.fullName.split(' ').first;
          _totalReports = reports.length;
          _favouriteReports = reports.where((r) => r.isFavourite).length;
          _recentReports = reports.take(3).toList();
          _activeReminders = reminders.length;
          _healthScore = score;
          _totalLabValues = totalLab;
          _abnormalCount = abnormal;
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
      body: SafeArea(
        child: Column(
          children: [
            const OfflineBanner(),
            Expanded(
              child: RefreshIndicator(
                onRefresh: _loadData,
          child: _loading
              ? const Padding(
                  padding: EdgeInsets.all(22),
                  child: SkeletonDashboard(),
                )
              : SingleChildScrollView(
            padding: const EdgeInsets.all(22),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DashboardHeader(name: _userName),
                const SizedBox(height: 30),
                HealthScoreCard(
                  score: _healthScore,
                  totalLabValues: _totalLabValues,
                  abnormalCount: _abnormalCount,
                ),
                const SizedBox(height: 30),

                // Statistics
                Row(
                  children: [
                    DashboardStatisticsCard(
                      title: AppLocalizations.of(context)!.statReports,
                      value: _totalReports.toString(),
                      icon: Icons.description_outlined,
                      color: Colors.blue,
                    ),
                    const SizedBox(width: 12),
                    DashboardStatisticsCard(
                      title: AppLocalizations.of(context)!.statReminders,
                      value: _activeReminders.toString(),
                      icon: Icons.medication_outlined,
                      color: Colors.orange,
                    ),
                    const SizedBox(width: 12),
                    DashboardStatisticsCard(
                      title: AppLocalizations.of(context)!.statFavourites,
                      value: _favouriteReports.toString(),
                      icon: Icons.favorite_border,
                      color: Colors.red,
                    ),
                  ],
                ),
                const SizedBox(height: 35),

                // Quick Actions
                Text(AppLocalizations.of(context)!.quickActions, style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 24, fontWeight: FontWeight.bold)),
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
                      title: AppLocalizations.of(context)!.allReports,
                      onTap: () => context.push(Routes.reports),
                    ),
                    QuickActionCard(
                      icon: Icons.smart_toy_outlined,
                      title: AppLocalizations.of(context)!.aiChatTab,
                      onTap: () => context.push(Routes.aiChat),
                    ),
                    QuickActionCard(
                      icon: Icons.bar_chart_rounded,
                      title: AppLocalizations.of(context)!.insights,
                      onTap: () => context.push(Routes.insights),
                    ),
                  ],
                ),
                const SizedBox(height: 35),

                // Reminders
                const MedicineReminderCard(),
                const SizedBox(height: 35),

                // Recent Reports
                Text(AppLocalizations.of(context)!.recentReports, style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 24, fontWeight: FontWeight.bold)),
                const SizedBox(height: 20),
                if (_loading)
                  const Center(child: CircularProgressIndicator())
                else if (_recentReports.isEmpty)
                  Center(child: Text(AppLocalizations.of(context)!.noRecentReports, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54))))
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
          ],
        ),
      ),
    );
  }
}