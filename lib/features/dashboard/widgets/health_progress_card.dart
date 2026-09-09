import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';

class HealthProgressCard extends StatelessWidget {
  final int totalReportsCount;
  final int completedReportsCount;
  final int? currentScore;
  final int? previousScore;
  final bool hasPreviousPeriodData;
  final VoidCallback? onUploadTap;

  const HealthProgressCard({
    super.key,
    required this.totalReportsCount,
    required this.completedReportsCount,
    this.currentScore,
    this.previousScore,
    this.hasPreviousPeriodData = false,
    this.onUploadTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(
          color: isDark
              ? Colors.white.withValues(alpha: 0.06)
              : Colors.black.withValues(alpha: 0.05),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.04),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header Row
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.insights_rounded,
                  color: AppColors.primary,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                "Weekly Health Progress",
                style: TextStyle(
                  color: theme.colorScheme.onSurface,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),

          const SizedBox(height: 20),

          // Render Content based on actual data
          _buildContent(context, theme),
        ],
      ),
    );
  }

  Widget _buildContent(BuildContext context, ThemeData theme) {
    // STATE 1: Zero reports or missing score
    if (totalReportsCount == 0 || currentScore == null) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.10),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.health_and_safety_outlined,
                    size: 28,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(height: 14),
                Text(
                  "No health progress yet",
                  style: TextStyle(
                    color: theme.colorScheme.onSurface,
                    fontSize: 16.5,
                    fontWeight: FontWeight.w600,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 6),
                Text(
                  "Upload a medical report to start tracking your health progress.",
                  style: TextStyle(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.60),
                    fontSize: 13.5,
                    height: 1.4,
                  ),
                  textAlign: TextAlign.center,
                ),
                if (onUploadTap != null) ...[
                  const SizedBox(height: 18),
                  ElevatedButton.icon(
                    onPressed: onUploadTap,
                    icon: const Icon(Icons.add_rounded, size: 18),
                    label: const Text(
                      "Upload Report",
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 11),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      );
    }

    // STATE 2: 1 Report or insufficient comparison data
    if (!hasPreviousPeriodData || previousScore == null) {
      final double progressVal = (currentScore! / 100.0).clamp(0.0, 1.0);
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                "Current Score",
                style: TextStyle(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.70),
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
              Text(
                "$currentScore%",
                style: const TextStyle(
                  color: AppColors.primary,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: progressVal,
              minHeight: 10,
              backgroundColor: AppColors.primary.withValues(alpha: 0.12),
              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
            ),
          ),
          const SizedBox(height: 14),
          Text(
            completedReportsCount <= 1
                ? "Health tracking has started. More historical data is needed to show a weekly comparison."
                : "Not enough historical data for a weekly comparison.",
            style: TextStyle(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
              fontSize: 13.5,
              height: 1.45,
            ),
          ),
        ],
      );
    }

    // STATE 3: Sufficient comparable data -> calculate actual % change
    final int diff = currentScore! - previousScore!;
    final int pctChange = previousScore! > 0
        ? (((currentScore! - previousScore!) / previousScore!).abs() * 100).round()
        : 0;

    String textMsg;
    if (diff > 0) {
      textMsg = "Your health score improved by $pctChange% compared to last week.";
    } else if (diff < 0) {
      textMsg = "Your health score changed by $pctChange% compared to last week.";
    } else {
      textMsg = "Your health score is unchanged compared to last week.";
    }

    final double progressVal = (currentScore! / 100.0).clamp(0.0, 1.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              "Current Score",
              style: TextStyle(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.70),
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            Text(
              "$currentScore%",
              style: const TextStyle(
                color: AppColors.primary,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        ClipRRect(
          borderRadius: BorderRadius.circular(10),
          child: LinearProgressIndicator(
            value: progressVal,
            minHeight: 10,
            backgroundColor: AppColors.primary.withValues(alpha: 0.12),
            valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
          ),
        ),
        const SizedBox(height: 14),
        Text(
          textMsg,
          style: TextStyle(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.75),
            fontSize: 14,
            height: 1.45,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}