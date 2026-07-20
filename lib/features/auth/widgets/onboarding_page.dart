import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class OnboardingPage extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;

  const OnboardingPage({
    super.key,
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: 28,
        vertical: 30,
      ),

      child: Column(
        children: [

          const Spacer(),

          Container(
            height: 170,
            width: 170,

            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(40),
            ),

            child: Icon(
              icon,
              size: 90,
              color: AppColors.primary,
            ),
          ),

          const SizedBox(height: 60),

          Text(
            title,
            textAlign: TextAlign.center,

            style: const TextStyle(
              fontSize: 32,
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
              fontSize: 17,
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