import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class RecentReportCard extends StatelessWidget {
  final String title;
  final String hospital;
  final String date;
  final IconData icon;

  const RecentReportCard({
    super.key,
    required this.title,
    required this.hospital,
    required this.date,
    this.icon = Icons.description_outlined,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 15),
      padding: const EdgeInsets.all(18),

      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(22),
      ),

      child: Row(
        children: [

          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: .12),
              borderRadius: BorderRadius.circular(15),
            ),

            child: Icon(
              icon,
              color: AppColors.primary,
            ),
          ),

          SizedBox(width: 16),

          Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,

              children: [

                Text(
                  title,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface,
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                SizedBox(height: 5),

                Text(
                  hospital,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.60),
                  ),
                ),

                SizedBox(height: 3),

                Text(
                  date,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.38),
                  ),
                ),

              ],
            ),
          ),

          Icon(
            Icons.arrow_forward_ios,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.38),
            size: 18,
          )

        ],
      ),
    );
  }
}