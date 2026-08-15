import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';

class LabResultRow extends StatelessWidget {
  final String parameter;
  final String unit;
  final double value;
  final double minRange;
  final double maxRange;
  final VoidCallback onTap;

  const LabResultRow({
    super.key,
    required this.parameter,
    required this.unit,
    required this.value,
    required this.minRange,
    required this.maxRange,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    bool isLow = value < minRange;
    bool isHigh = value > maxRange;
    bool isNormal = !isLow && !isHigh;

    Color statusColor = isNormal ? Colors.green : Colors.red;
    
    // Calculate progress bar positioning
    double rangeDiff = maxRange - minRange;
    double normalizedValue = 0.5; // Default center
    if (rangeDiff > 0) {
      normalizedValue = (value - minRange) / rangeDiff;
    }
    
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
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
                      Text(parameter, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16, color: Theme.of(context).colorScheme.onSurface)),
                      SizedBox(height: 2),
                      Text(unit, style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5))),
                    ],
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Center(
                    child: Text(
                      value.toString(),
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: statusColor),
                    ),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Align(
                    alignment: Alignment.centerRight,
                    child: Text(
                      '$minRange - $maxRange',
                      style: TextStyle(fontSize: 12, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5)),
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 12),
            Stack(
              clipBehavior: Clip.none,
              children: [
                Container(
                  height: 4,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                Positioned(
                  left: 0,
                  right: 0,
                  top: 0,
                  child: Row(
                    children: [
                      Expanded(
                        child: LayoutBuilder(
                          builder: (context, constraints) {
                            double indicatorLeft = constraints.maxWidth * normalizedValue.clamp(0.0, 1.0);
                            if (isLow) indicatorLeft = 0;
                            if (isHigh) indicatorLeft = constraints.maxWidth - 8;
                            
                            return Stack(
                              clipBehavior: Clip.none,
                              children: [
                                SizedBox(height: 4, width: constraints.maxWidth),
                                Positioned(
                                  left: indicatorLeft - 4,
                                  top: -2,
                                  child: Container(
                                    width: 8,
                                    height: 8,
                                    decoration: BoxDecoration(
                                      color: statusColor,
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                ),
                              ],
                            );
                          }
                        ),
                      ),
                    ],
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
