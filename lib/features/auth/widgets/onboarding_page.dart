import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../shared/widgets/illustrations.dart';

/// OnboardingPage that replaces the generic icon with our custom medical illustrations.
class OnboardingPage extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final int pageIndex;

  const OnboardingPage({
    super.key,
    required this.icon,
    required this.title,
    required this.subtitle,
    this.pageIndex = 0,
  });

  Widget _illustration() {
    switch (pageIndex) {
      case 0:
        return const OnboardingIllustration1();
      case 1:
        return const OnboardingIllustration2();
      case 2:
        return const OnboardingIllustration3();
      default:
        return Container(
          height: 170,
          width: 170,
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(40),
          ),
          child: Icon(icon, size: 90, color: AppColors.primary),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 30),
      child: Column(
        children: [
          const Spacer(),
          _illustration(),
          const SizedBox(height: 50),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 30,
              fontWeight: FontWeight.bold,
              color: Colors.white,
              height: 1.2,
            ),
          ),
          const SizedBox(height: 20),
          Text(
            subtitle,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 16,
              color: AppColors.textSecondary,
              height: 1.6,
            ),
          ),
          const Spacer(),
        ],
      ),
    );
  }
}