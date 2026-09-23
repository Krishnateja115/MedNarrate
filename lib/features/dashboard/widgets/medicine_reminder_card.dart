import 'package:flutter/material.dart';
import '../../../core/services/reminder_service.dart';

class MedicineReminderCard extends StatelessWidget {
  final List<ReminderModel> reminders;
  final List<Map<String, dynamic>> reportedMedications;
  final VoidCallback? onAddTap;
  final void Function(Map<String, dynamic>)? onConfirmTap;

  const MedicineReminderCard({
    super.key,
    required this.reminders,
    this.reportedMedications = const [],
    this.onAddTap,
    this.onConfirmTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final hasReportedMeds = reportedMedications.isNotEmpty;
    final hasManualMeds = reminders.isNotEmpty;

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
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
              if (onAddTap != null)
                IconButton(
                  onPressed: onAddTap,
                  icon: const Icon(Icons.add_circle_outline_rounded, color: Colors.orange),
                  tooltip: "Add Medicine",
                ),
            ],
          ),

          const SizedBox(height: 16),

          if (!hasReportedMeds && !hasManualMeds)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Center(
                child: Column(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: Colors.orange.withValues(alpha: 0.10),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.medication_liquid_outlined,
                        size: 24,
                        color: Colors.orange,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      "No medicines added yet",
                      style: TextStyle(
                        color: theme.colorScheme.onSurface,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      "Add a medication or upload a report containing medication information.",
                      style: TextStyle(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.60),
                        fontSize: 13,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    if (onAddTap != null) ...[
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.orange,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        onPressed: onAddTap,
                        icon: const Icon(Icons.add, size: 18),
                        label: const Text("Add a Medication"),
                      ),
                    ],
                  ],
                ),
              ),
            )
          else ...[
            // Report Extracted Medications
            if (hasReportedMeds) ...[
              Row(
                children: [
                  Text(
                    "Medications from Latest Report",
                    style: TextStyle(
                      color: theme.colorScheme.primary,
                      fontSize: 13.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      "Reported",
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              ...reportedMedications.map((med) {
                final name = med['medication_name'] ?? med['name'] ?? 'Medication';
                final dosage = med['dosage'] as String?;
                final frequency = med['frequency'] as String?;
                final times = med['times_of_day'] as List<dynamic>? ?? [];

                String timingStr = times.isNotEmpty ? times.join(', ') : 'Timing: Not specified';

                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.03),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 16,
                        backgroundColor: const Color(0xFFFFF3E0),
                        child: const Icon(Icons.medication, size: 16, color: Colors.orange),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              name,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14.5,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              [
                                if (dosage != null && dosage.isNotEmpty) dosage,
                                if (frequency != null && frequency.isNotEmpty) frequency,
                                timingStr,
                              ].join(' • '),
                              style: TextStyle(
                                fontSize: 12,
                                color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (onConfirmTap != null)
                        IconButton(
                          onPressed: () => onConfirmTap!(med),
                          icon: const Icon(Icons.check_circle_outline, color: Colors.green),
                          tooltip: "Confirm to Schedule",
                        ),
                    ],
                  ),
                );
              }),
            ],

            // User Manual Medications
            if (hasManualMeds) ...[
              if (hasReportedMeds) const SizedBox(height: 14),
              Text(
                "My Confirmed Schedule",
                style: TextStyle(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  fontSize: 13.5,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              ...reminders.map((reminder) {
                final timeFormatted = TimeOfDay.fromDateTime(reminder.time).format(context);
                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.03),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.alarm, size: 18, color: Colors.orange),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          reminder.medicineName,
                          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                        ),
                      ),
                      Text(
                        timeFormatted,
                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.orange),
                      ),
                    ],
                  ),
                );
              }),
            ],
          ],
        ],
      ),
    );
  }
}