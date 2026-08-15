import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class ReportTimelineTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final String date;
  final bool isFirst;
  final bool isLast;
  final Color? color;
  final VoidCallback? onTap;

  const ReportTimelineTile({
    super.key,
    required this.title,
    required this.subtitle,
    required this.date,
    this.isFirst = false,
    this.isLast = false,
    this.color,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final tileColor = color ?? AppColors.primary;

    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(
          vertical: 10,
          horizontal: 6,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 36,
              child: Column(
                children: [
                  if (!isFirst)
                    Container(
                      width: 2,
                      height: 18,
                      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.24),
                    ),

                  Container(
                    width: 14,
                    height: 14,
                    decoration: BoxDecoration(
                      color: tileColor,
                      shape: BoxShape.circle,
                    ),
                  ),

                  if (!isLast)
                    Container(
                      width: 2,
                      height: 70,
                      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.24),
                    ),
                ],
              ),
            ),

            SizedBox(width: 14),

            Expanded(
              child: Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Theme.of(context).cardColor,
                  borderRadius: BorderRadius.circular(18),
                ),
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

                    SizedBox(height: 8),

                    Text(
                      subtitle,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70),
                        fontSize: 14,
                      ),
                    ),

                    SizedBox(height: 10),

                    Row(
                      children: [
                        Icon(
                          Icons.calendar_today,
                          size: 16,
                          color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54),
                        ),

                        SizedBox(width: 6),

                        Text(
                          date,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54),
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}