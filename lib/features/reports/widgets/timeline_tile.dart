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
                      color: Colors.white24,
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
                      color: Colors.white24,
                    ),
                ],
              ),
            ),

            const SizedBox(width: 14),

            Expanded(
              child: Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                      ),
                    ),

                    const SizedBox(height: 8),

                    Text(
                      subtitle,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                      ),
                    ),

                    const SizedBox(height: 10),

                    Row(
                      children: [
                        const Icon(
                          Icons.calendar_today,
                          size: 16,
                          color: Colors.white54,
                        ),

                        const SizedBox(width: 6),

                        Text(
                          date,
                          style: const TextStyle(
                            color: Colors.white54,
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