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
import '../widgets/recent_reports_section.dart';
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
  List<ReminderModel> _remindersList = [];
  int _healthScore = 0;
  int _totalLabValues = 0;
  int _abnormalCount = 0;
  int _completedReportsCount = 0;
  int? _currentPeriodScore;
  int? _previousPeriodScore;
  bool _hasPreviousPeriodData = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<int?> _calculateScoreForReport(String reportId) async {
    try {
      final analysis = await ApiService.instance.getReportAnalysis(reportId);
      if (analysis.structuredLabValues.isEmpty) return 100;
      final total = analysis.structuredLabValues.length;
      final abnormal = analysis.structuredLabValues.where((v) => v.flag != 'normal').length;
      return (((total - abnormal) / total) * 100).round();
    } catch (_) {
      return null;
    }
  }

  Future<void> _loadData() async {
    try {
      final user = await ApiService.instance.getMe();
      final reports = await ApiService.instance.listReports();
      final reminders = await ReminderService.instance.getAll();

      final completed = reports.where((r) => r.processingStatus == 'completed').toList();
      completed.sort((a, b) => b.reportDate.compareTo(a.reportDate));

      int? currentPeriodScore;
      int? previousPeriodScore;
      bool hasPreviousData = false;

      if (completed.isNotEmpty) {
        currentPeriodScore = await _calculateScoreForReport(completed.first.id);
        if (completed.length > 1) {
          final latestDate = completed.first.reportDate;
          final prevReport = completed.firstWhere(
            (r) => latestDate.difference(r.reportDate).inDays.abs() >= 1,
            orElse: () => completed[1],
          );
          if (prevReport.id != completed.first.id) {
            previousPeriodScore = await _calculateScoreForReport(prevReport.id);
            hasPreviousData = previousPeriodScore != null;
          }
        }
      }

      int totalLab = 0;
      int abnormal = 0;
      if (completed.isNotEmpty && currentPeriodScore != null) {
        try {
          final analysis = await ApiService.instance.getReportAnalysis(completed.first.id);
          totalLab = analysis.structuredLabValues.length;
          abnormal = analysis.structuredLabValues.where((v) => v.flag != 'normal').length;
        } catch (_) {}
      }
      final score = currentPeriodScore ?? 0;

      if (mounted) {
        setState(() {
          _userName = user.fullName.split(' ').first;
          _totalReports = reports.length;
          _completedReportsCount = completed.length;
          _favouriteReports = reports.where((r) => r.isFavourite).length;
          _recentReports = reports.take(3).toList();
          _activeReminders = reminders.length;
          _remindersList = reminders;
          _healthScore = score;
          _totalLabValues = totalLab;
          _abnormalCount = abnormal;
          _currentPeriodScore = currentPeriodScore;
          _previousPeriodScore = previousPeriodScore;
          _hasPreviousPeriodData = hasPreviousData;
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
                MedicineReminderCard(
                  reminders: _remindersList,
                  onAddTap: () async {
                    await context.push(Routes.upload);
                    _loadData();
                  },
                ),
                const SizedBox(height: 35),

                // Recent Reports
                RecentReportsSection(
                  loading: _loading,
                  reports: _recentReports,
                  onViewAllTap: () => context.push(Routes.reports),
                  onUploadTap: () async {
                    await context.push(Routes.upload);
                    _loadData();
                  },
                  onReportTap: (report) => context.push(Routes.reportDetails, extra: report.id),
                ),
                const SizedBox(height: 35),

                const HealthTipCard(),
                const SizedBox(height: 30),
                HealthProgressCard(
                  totalReportsCount: _totalReports,
                  completedReportsCount: _completedReportsCount,
                  currentScore: _currentPeriodScore,
                  previousScore: _previousPeriodScore,
                  hasPreviousPeriodData: _hasPreviousPeriodData,
                  onUploadTap: () async {
                    await context.push(Routes.upload);
                    _loadData();
                  },
                ),
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