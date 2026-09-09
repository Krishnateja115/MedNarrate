import 'package:flutter/material.dart';

import '../../../core/services/reminder_service.dart';

class MedicineReminderCard extends StatelessWidget {
  final List<ReminderModel> reminders;
  final VoidCallback? onAddTap;

  const MedicineReminderCard({
    super.key,
    required this.reminders,
    this.onAddTap,
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
                  color: Colors.orange.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.medication_outlined,
                  color: Colors.orange,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                "Today's Medicine",
                style: TextStyle(
                  color: theme.colorScheme.onSurface,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),

          const SizedBox(height: 20),

          // Content
          if (reminders.isEmpty)
            Padding(
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
                          color: Colors.orange.withValues(alpha: 0.10),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.medication_liquid_outlined,
                          size: 28,
                          color: Colors.orange,
                        ),
                      ),
                      const SizedBox(height: 14),
                      Text(
                        "No medicines added yet",
                        style: TextStyle(
                          color: theme.colorScheme.onSurface,
                          fontSize: 16.5,
                          fontWeight: FontWeight.w600,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 6),
                      Text(
                        "Add a medication or upload a prescription to see your schedule here.",
                        style: TextStyle(
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.60),
                          fontSize: 13.5,
                          height: 1.4,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      if (onAddTap != null) ...[
                        const SizedBox(height: 18),
                        ElevatedButton.icon(
                          onPressed: onAddTap,
                          icon: const Icon(Icons.add_rounded, size: 18),
                          label: const Text(
                            "Add Medicine",
                            style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.orange.shade700,
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
            )
          else
            Column(
              children: reminders.asMap().entries.map((entry) {
                final index = entry.key;
                final reminder = entry.value;
                final isLast = index == reminders.length - 1;
                final timeFormatted = TimeOfDay.fromDateTime(reminder.time).format(context);

                return Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                      child: Row(
                        children: [
                          CircleAvatar(
                            radius: 22,
                            backgroundColor: Colors.orange.withValues(alpha: 0.15),
                            child: const Icon(
                              Icons.medication,
                              color: Colors.orange,
                              size: 22,
                            ),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  reminder.medicineName,
                                  style: TextStyle(
                                    color: theme.colorScheme.onSurface,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                  ),
                                ),
                                if (reminder.dosageNote != null &&
                                    reminder.dosageNote!.trim().isNotEmpty) ...[
                                  const SizedBox(height: 3),
                                  Text(
                                    reminder.dosageNote!,
                                    style: TextStyle(
                                      color: theme.colorScheme.onSurface
                                          .withValues(alpha: 0.60),
                                      fontSize: 13,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                            decoration: BoxDecoration(
                              color: Colors.orange.withValues(alpha: 0.10),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              timeFormatted,
                              style: TextStyle(
                                color: Colors.orange.shade800,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (!isLast)
                      Divider(
                        height: 1,
                        thickness: 1,
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.06),
                      ),
                  ],
                );
              }).toList(),
            ),
        ],
      ),
    );
  }
}