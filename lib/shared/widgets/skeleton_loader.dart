import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';

import '../../core/constants/app_colors.dart';

/// Reusable shimmer skeleton box.
class SkeletonBox extends StatelessWidget {
  final double width;
  final double height;
  final double radius;

  const SkeletonBox({
    super.key,
    this.width = double.infinity,
    this.height = 16,
    this.radius = 8,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Shimmer.fromColors(
      baseColor: isDark ? const Color(0xFF1C2128) : const Color(0xFFE0E0E0),
      highlightColor: isDark ? const Color(0xFF2D333B) : const Color(0xFFF5F5F5),
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: isDark ? const Color(0xFF1C2128) : const Color(0xFFE0E0E0),
          borderRadius: BorderRadius.circular(radius),
        ),
      ),
    );
  }
}

/// Skeleton for a report card in the list.
class SkeletonReportCard extends StatelessWidget {
  const SkeletonReportCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const SkeletonBox(width: 40, height: 40, radius: 12),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    SkeletonBox(height: 14, radius: 6),
                    SizedBox(height: 8),
                    SkeletonBox(width: 120, height: 11, radius: 6),
                  ],
                ),
              ),
              const SkeletonBox(width: 60, height: 22, radius: 100),
            ],
          ),
        ],
      ),
    );
  }
}

/// Skeleton for the analysis screen while loading.
class SkeletonAnalysis extends StatelessWidget {
  const SkeletonAnalysis({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SkeletonBox(height: 20, radius: 8),
          const SizedBox(height: 12),
          const SkeletonBox(height: 14, width: 200, radius: 6),
          const SizedBox(height: 24),
          const SkeletonBox(height: 120, radius: 16),
          const SizedBox(height: 20),
          const SkeletonBox(height: 14, width: 160, radius: 6),
          const SizedBox(height: 12),
          ...List.generate(3, (_) => const Padding(
            padding: EdgeInsets.only(bottom: 10),
            child: SkeletonBox(height: 70, radius: 12),
          )),
          const SizedBox(height: 20),
          const SkeletonBox(height: 14, width: 140, radius: 6),
          const SizedBox(height: 12),
          ...List.generate(4, (_) => const Padding(
            padding: EdgeInsets.only(bottom: 10),
            child: SkeletonBox(height: 50, radius: 12),
          )),
        ],
      ),
    );
  }
}

/// Skeleton for the dashboard stats row.
class SkeletonDashboard extends StatelessWidget {
  const SkeletonDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SkeletonBox(height: 90, radius: 20),
        const SizedBox(height: 20),
        Row(
          children: [
            const Expanded(child: SkeletonBox(height: 80, radius: 16)),
            const SizedBox(width: 10),
            const Expanded(child: SkeletonBox(height: 80, radius: 16)),
            const SizedBox(width: 10),
            const Expanded(child: SkeletonBox(height: 80, radius: 16)),
          ],
        ),
        const SizedBox(height: 20),
        ...List.generate(3, (_) => const Padding(
          padding: EdgeInsets.only(bottom: 12),
          child: SkeletonReportCard(),
        )),
      ],
    );
  }
}
