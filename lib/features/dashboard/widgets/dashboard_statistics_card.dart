import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class DashboardStatisticsCard extends StatelessWidget {

  final String title;

  final String value;

  final IconData icon;

  final Color color;

  const DashboardStatisticsCard({

    super.key,

    required this.title,

    required this.value,

    required this.icon,

    required this.color,

  });

  @override
  Widget build(BuildContext context) {

    return Expanded(

      child: Container(

        padding: const EdgeInsets.all(18),

        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: AppColors.border, width: 1),
        ),
        child: Column(
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                shape: BoxShape.circle,
                border: Border.all(color: color.withValues(alpha: 0.3), width: 1),
              ),
              child: Icon(
                icon,
                color: Theme.of(context).colorScheme.onSurface,
                size: 24,
              ),
            ),

            SizedBox(height: 15),

            Text(

              value,

              style: TextStyle(

                color: Theme.of(context).colorScheme.onSurface,

                fontWeight: FontWeight.bold,

                fontSize: 24,

              ),

            ),

            SizedBox(height: 5),

            Text(

              title,

              textAlign: TextAlign.center,

              style: TextStyle(

                color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.60),

              ),

            ),

          ],

        ),

      ),

    );

  }

}