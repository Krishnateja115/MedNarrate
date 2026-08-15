class MedicationScheduleModel {
  final String id;
  final String reportId;
  final String medicationName;
  final String? dosage;
  final String? frequency;
  final List<String> timesOfDay;
  final int? durationDays;
  final String? notes;
  final bool isActive;
  final DateTime createdAt;

  MedicationScheduleModel({
    required this.id,
    required this.reportId,
    required this.medicationName,
    this.dosage,
    this.frequency,
    required this.timesOfDay,
    this.durationDays,
    this.notes,
    required this.isActive,
    required this.createdAt,
  });

  factory MedicationScheduleModel.fromMap(Map<String, dynamic> map) {
    return MedicationScheduleModel(
      id: map['id'] as String,
      reportId: map['report_id'] as String,
      medicationName: map['medication_name'] as String,
      dosage: map['dosage'] as String?,
      frequency: map['frequency'] as String?,
      timesOfDay: List<String>.from(map['times_of_day'] ?? []),
      durationDays: map['duration_days'] as int?,
      notes: map['notes'] as String?,
      isActive: map['is_active'] as bool,
      createdAt: DateTime.parse(map['created_at'] as String),
    );
  }
}
