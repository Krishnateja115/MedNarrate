import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../l10n/app_l10n.dart';
import 'notification_service.dart';
import 'secure_storage_config.dart';
import 'storage_service.dart';

class MedicationAlert {
  final DateTime when;
  final String title;
  final String body;
  final bool repeatDaily;

  const MedicationAlert(this.when, this.title, this.body, this.repeatDaily);
}

final RegExp _clockPattern = RegExp(
  r'^\s*(\d{1,2})(?:[:.](\d{2}))?(?::\d{2})?\s*([ap])?\.?\s*(?:m\.?)?\s*$',
  caseSensitive: false,
);

/// Parses "08:00", "8:00 AM", "8 pm", "08.30 a.m." or "20:00:00" into
/// `[hour24, minute]`, or null when [raw] is not a clock time. Report-extracted
/// schedules may use AM/PM; reminders created in the app use 24-hour HH:MM.
List<int>? parseClockTime(String raw) {
  final match = _clockPattern.firstMatch(raw);
  if (match == null) return null;
  var hour = int.parse(match.group(1)!);
  final minuteText = match.group(2);
  final minute = minuteText == null ? 0 : int.parse(minuteText);
  final meridiem = match.group(3)?.toLowerCase();
  // A bare number ("3") is a count, not a time of day.
  if (minuteText == null && meridiem == null) return null;
  if (minute > 59) return null;
  if (meridiem != null) {
    if (hour < 1 || hour > 12) return null;
    hour = hour % 12 + (meridiem == 'p' ? 12 : 0);
  } else if (hour > 23) {
    return null;
  }
  return [hour, minute];
}

/// Converts the account's medicine schedules into phone-local alert times.
/// A finite course uses one-shot alerts so it cannot keep notifying after it ends.
List<MedicationAlert> planMedicationAlerts(
  List<Map<String, dynamic>> reminders,
  DateTime now,
) {
  final alerts = <MedicationAlert>[];
  final today = DateTime(now.year, now.month, now.day);
  for (final reminder in reminders) {
    if (reminder['is_active'] != true) continue;
    // "As needed" medicine has no scheduled dose to alert for.
    if (reminder['frequency']?.toString().toLowerCase() == 'as needed') {
      continue;
    }
    final name = reminder['medication_name']?.toString().trim() ?? '';
    if (name.isEmpty) continue;
    final dosage = reminder['dosage']?.toString().trim() ?? '';
    final title = appL10n.medAlertTitle(name);
    final body = dosage.isEmpty ? appL10n.medAlertBody : dosage;
    final duration = reminder['duration_days'] as int?;
    final createdRaw = reminder['created_at']?.toString();
    final created = createdRaw == null
        ? now
        : DateTime.tryParse(
              createdRaw.endsWith('Z') ||
                      RegExp(r'[+-]\d\d:\d\d$').hasMatch(createdRaw)
                  ? createdRaw
                  : '${createdRaw}Z',
            )?.toLocal() ??
            now;
    final start = DateTime(created.year, created.month, created.day);
    final end = duration == null
        ? null
        : DateTime(start.year, start.month, start.day + duration);
    final rawTimes = reminder['times_of_day'];
    if (rawTimes is! List) continue;
    for (final rawTime in rawTimes) {
      final parsed = parseClockTime(rawTime.toString());
      if (parsed == null) continue;
      final hour = parsed[0];
      final minute = parsed[1];
      if (end == null) {
        var next = DateTime(today.year, today.month, today.day, hour, minute);
        if (!next.isAfter(now)) {
          next = DateTime(today.year, today.month, today.day + 1, hour, minute);
        }
        alerts.add(MedicationAlert(next, title, body, true));
      } else {
        // Schedule a rolling year; revisiting the app refreshes longer courses.
        final horizon = DateTime(today.year, today.month, today.day + 365);
        for (var day = start.isAfter(today) ? start : today;
            day.isBefore(end) && day.isBefore(horizon);
            day = DateTime(day.year, day.month, day.day + 1)) {
          final occurrence =
              DateTime(day.year, day.month, day.day, hour, minute);
          if (occurrence.isAfter(now)) {
            alerts.add(MedicationAlert(occurrence, title, body, false));
          }
        }
      }
    }
  }
  alerts.sort((a, b) => a.when.compareTo(b.when));
  // iOS keeps only 64 pending notifications; leave four slots for other alerts.
  if (defaultTargetPlatform == TargetPlatform.iOS && alerts.length > 60) {
    return alerts.take(60).toList();
  }
  return alerts;
}

class MedicationAlertService {
  MedicationAlertService._();
  static final instance = MedicationAlertService._();
  static const _scheduledIdsKey = 'scheduled_medication_alert_ids';
  static const _remindersKey = 'local_medication_alert_source';
  final FlutterSecureStorage _storage = appSecureStorage;
  Future<void> _tail = Future<void>.value();

  Future<void> sync(List<Map<String, dynamic>> reminders) => _enqueue(() async {
        await _apply(reminders);
      });

  Future<void> upsert(Map<String, dynamic> reminder) => _enqueue(() async {
        final reminders = await _readReminders();
        reminders.removeWhere((item) => item['id'] == reminder['id']);
        reminders.add(reminder);
        await _apply(reminders);
      });

  Future<void> remove(String id) => _enqueue(() async {
        final reminders = await _readReminders();
        reminders.removeWhere((item) => item['id'] == id);
        await _apply(reminders);
      });

  Future<void> toggle(String id) => _enqueue(() async {
        final reminders = await _readReminders();
        for (final reminder in reminders) {
          if (reminder['id'] == id) {
            reminder['is_active'] = reminder['is_active'] != true;
          }
        }
        await _apply(reminders);
      });

  Future<void> syncCached() => _enqueue(() async {
        await _apply(await _readReminders());
      });

  Future<void> _apply(List<Map<String, dynamic>> reminders) async {
    if (kIsWeb) return;
    await _storage.write(key: _remindersKey, value: jsonEncode(reminders));
    final previous = await _readIds();
    for (final id in previous) {
      await NotificationService.instance.cancelReminder(id);
    }
    final enabled = await StorageService.instance.getNotificationsEnabled();
    if (!enabled || !NotificationService.instance.notificationsAllowed) {
      await _writeIds([]);
      return;
    }
    final alerts = planMedicationAlerts(reminders, DateTime.now());
    final ids = List<int>.generate(alerts.length, (i) => 0x40000000 + i);
    // Persist before scheduling, so an interrupted sync is recoverable.
    await _writeIds(ids);
    for (var i = 0; i < alerts.length; i++) {
      final alert = alerts[i];
      await NotificationService.instance.scheduleDailyReminder(
        ids[i],
        alert.title,
        alert.body,
        alert.when,
        repeatDaily: alert.repeatDaily,
      );
    }
  }

  Future<void> clear() => _enqueue(() async {
        if (kIsWeb) return;
        for (final id in await _readIds()) {
          await NotificationService.instance.cancelReminder(id);
        }
        await _storage.delete(key: _scheduledIdsKey);
        await _storage.delete(key: _remindersKey);
      });

  Future<void> _enqueue(Future<void> Function() operation) {
    final result = _tail.then((_) => operation());
    _tail = result.catchError((Object error) {
      debugPrint('Medication alert sync failed: $error');
    });
    return result;
  }

  Future<List<int>> _readIds() async {
    final raw = await _storage.read(key: _scheduledIdsKey);
    if (raw == null) return [];
    return (jsonDecode(raw) as List<dynamic>).cast<int>();
  }

  Future<List<Map<String, dynamic>>> _readReminders() async {
    if (kIsWeb) return [];
    final raw = await _storage.read(key: _remindersKey);
    if (raw == null) return [];
    return List<Map<String, dynamic>>.from(jsonDecode(raw) as List<dynamic>);
  }

  Future<void> _writeIds(List<int> ids) =>
      _storage.write(key: _scheduledIdsKey, value: jsonEncode(ids));
}
