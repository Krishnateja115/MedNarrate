import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/features/reminders/models/medication_schedule_model.dart';

// Simple standalone MedicationCard widget for testability
class MedicationCard extends StatelessWidget {
  final MedicationScheduleModel medication;
  const MedicationCard({Key? key, required this.medication}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              medication.medicationName,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            if (medication.dosage != null)
              Text('Dosage: ${medication.dosage}'),
            if (medication.frequency != null)
              Text('Frequency: ${medication.frequency}'),
            if (medication.timesOfDay.isNotEmpty)
              Text('Times: ${medication.timesOfDay.join(', ')}'),
            if (medication.durationDays != null)
              Text('Duration: ${medication.durationDays} days'),
            if (medication.notes != null)
              Text('Notes: ${medication.notes}'),
          ],
        ),
      ),
    );
  }
}

void main() {
  final mockMedication = MedicationScheduleModel(
    id: 'med-001',
    reportId: 'report-001',
    medicationName: 'Metformin',
    dosage: '500mg',
    frequency: 'twice daily',
    timesOfDay: ['08:00', '20:00'],
    durationDays: 30,
    notes: 'Take with food',
    isActive: true,
    createdAt: DateTime(2024, 1, 15),
  );

  group('MedicationCard Widget', () {
    testWidgets('renders medication name', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MedicationCard(medication: mockMedication),
          ),
        ),
      );
      expect(find.text('Metformin'), findsOneWidget);
    });

    testWidgets('renders dosage information', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MedicationCard(medication: mockMedication),
          ),
        ),
      );
      expect(find.text('Dosage: 500mg'), findsOneWidget);
    });

    testWidgets('renders frequency information', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MedicationCard(medication: mockMedication),
          ),
        ),
      );
      expect(find.text('Frequency: twice daily'), findsOneWidget);
    });

    testWidgets('renders times of day', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MedicationCard(medication: mockMedication),
          ),
        ),
      );
      expect(find.text('Times: 08:00, 20:00'), findsOneWidget);
    });

    testWidgets('renders duration', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MedicationCard(medication: mockMedication),
          ),
        ),
      );
      expect(find.text('Duration: 30 days'), findsOneWidget);
    });

    testWidgets('renders notes', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MedicationCard(medication: mockMedication),
          ),
        ),
      );
      expect(find.text('Notes: Take with food'), findsOneWidget);
    });

    testWidgets('renders without optional fields gracefully', (tester) async {
      final minimal = MedicationScheduleModel(
        id: 'med-002',
        reportId: 'report-001',
        medicationName: 'Aspirin',
        timesOfDay: [],
        isActive: true,
        createdAt: DateTime(2024, 1, 15),
      );
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MedicationCard(medication: minimal),
          ),
        ),
      );
      expect(find.text('Aspirin'), findsOneWidget);
      // No dosage, frequency, notes should be shown
      expect(find.textContaining('Dosage'), findsNothing);
      expect(find.textContaining('Frequency'), findsNothing);
    });
  });

  group('MedicationScheduleModel', () {
    test('fromMap creates model correctly', () {
      final map = {
        'id': 'med-003',
        'report_id': 'report-002',
        'medication_name': 'Lisinopril',
        'dosage': '10mg',
        'frequency': 'once daily',
        'times_of_day': ['09:00'],
        'duration_days': 90,
        'notes': null,
        'is_active': true,
        'created_at': '2024-01-15T00:00:00.000',
      };
      final model = MedicationScheduleModel.fromMap(map);
      expect(model.medicationName, equals('Lisinopril'));
      expect(model.dosage, equals('10mg'));
      expect(model.frequency, equals('once daily'));
      expect(model.timesOfDay, equals(['09:00']));
      expect(model.durationDays, equals(90));
      expect(model.notes, isNull);
      expect(model.isActive, isTrue);
    });

    test('fromMap handles empty times_of_day', () {
      final map = {
        'id': 'med-004',
        'report_id': 'report-003',
        'medication_name': 'Test Med',
        'times_of_day': null,
        'is_active': false,
        'created_at': '2024-01-15T00:00:00.000',
      };
      final model = MedicationScheduleModel.fromMap(map);
      expect(model.timesOfDay, isEmpty);
      expect(model.isActive, isFalse);
    });
  });
}
