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

  test('AM/PM times extracted from reports are scheduled', () {
    final alerts = planMedicationAlerts([
      reminder(times: ['08:00 AM', '8:30 pm', '09.15 a.m.']),
    ], now);
    expect(alerts.map((alert) => alert.when), [
      DateTime(2026, 10, 11, 20, 30),
      DateTime(2026, 10, 12, 8),
      DateTime(2026, 10, 12, 9, 15),
    ]);
  });

  test('parseClockTime handles edge cases', () {
    expect(parseClockTime('12:00 AM'), [0, 0]);
    expect(parseClockTime('12:30 PM'), [12, 30]);
    expect(parseClockTime('20:00:00'), [20, 0]);
    expect(parseClockTime('3'), isNull);
    expect(parseClockTime('13:00 PM'), isNull);
    expect(parseClockTime('after breakfast'), isNull);
  });
}
