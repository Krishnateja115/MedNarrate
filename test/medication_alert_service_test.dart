import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/medication_alert_service.dart';

void main() {
  final now = DateTime(2026, 10, 11, 9, 30);

  Map<String, dynamic> reminder({
    bool active = true,
    List<String> times = const ['08:00', '20:00'],
    int? duration,
  }) =>
      {
        'medication_name': 'Example medicine',
        'dosage': '1 tablet',
        'is_active': active,
        'times_of_day': times,
        'duration_days': duration,
        'created_at': now.toUtc().toIso8601String(),
      };

  test('daily reminders roll passed times to tomorrow', () {
    final alerts = planMedicationAlerts([reminder()], now);
    expect(alerts, hasLength(2));
    expect(alerts[0].when, DateTime(2026, 10, 11, 20));
    expect(alerts[1].when, DateTime(2026, 10, 12, 8));
    expect(alerts.every((alert) => alert.repeatDaily), isTrue);
  });

  test('inactive reminders and invalid times do not schedule', () {
    final asNeeded = reminder();
    asNeeded['frequency'] = 'As needed';
    final alerts = planMedicationAlerts([
      reminder(active: false),
      reminder(times: ['25:00', 'bad', '12:61']),
      asNeeded,
    ], now);
    expect(alerts, isEmpty);
  });

  test('finite course stops at its end rather than repeating forever', () {
    final alerts = planMedicationAlerts([
      reminder(duration: 2, times: ['20:00']),
    ], now);
    expect(alerts.map((alert) => alert.when), [
      DateTime(2026, 10, 11, 20),
      DateTime(2026, 10, 12, 20),
    ]);
    expect(alerts.every((alert) => !alert.repeatDaily), isTrue);
  });

  test('expired and zero-day courses do not schedule', () {
    final expired = reminder(duration: 1, times: ['20:00']);
    expired['created_at'] = DateTime(2026, 10, 1).toUtc().toIso8601String();
    expect(
        planMedicationAlerts([expired, reminder(duration: 0)], now), isEmpty);
  });
}
