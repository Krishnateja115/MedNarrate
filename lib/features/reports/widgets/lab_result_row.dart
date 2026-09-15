import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';

class LabResultRow extends StatelessWidget {
  final String parameter;
  final String unit;
  final double value;
  final double? minRange;
  final double? maxRange;
  final String flag;
  final VoidCallback onTap;

  const LabResultRow({
    super.key,
    required this.parameter,
    required this.unit,
    required this.value,
    this.minRange,
    this.maxRange,
    this.flag = 'not_classified',
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasRange = minRange != null && maxRange != null && (maxRange! > minRange!);

    Color statusColor = theme.colorScheme.onSurface;
    String badgeText = "Not Classified";

    if (flag == 'high') {
      statusColor = Colors.redAccent;
      badgeText = "HIGH";
    } else if (flag == 'low') {
      statusColor = Colors.orange;
      badgeText = "LOW";
    } else if (flag == 'critical') {
      statusColor = Colors.red.shade900;
      badgeText = "CRITICAL";
    } else if (flag == 'normal') {
      statusColor = Colors.green;
      badgeText = "NORMAL";
    }

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: theme.cardColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  flex: 3,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        parameter,
                        style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15, color: theme.colorScheme.onSurface),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        unit.isNotEmpty ? unit : 'Unit: -',
                        style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface.withValues(alpha: 0.5)),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Center(
                    child: Column(
                      children: [
                        Text(
                          value == value.roundToDouble() ? value.toInt().toString() : value.toString(),
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 17, color: statusColor),
                        ),
                        Container(
                          margin: const EdgeInsets.only(top: 2),
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                          decoration: BoxDecoration(
                            color: statusColor.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            badgeText,
                            style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: statusColor),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Align(
                    alignment: Alignment.centerRight,
                    child: Text(
                      hasRange ? '$minRange - $maxRange' : 'No ref range',
                      style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface.withValues(alpha: 0.5)),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
