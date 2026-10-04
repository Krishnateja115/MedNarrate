import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'notification_service.dart';
import 'secure_storage_config.dart';

class ReminderModel {
  final int id;
  final String medicineName;
  final String? dosageNote;
  final DateTime time;
  final bool repeatDaily;

  const ReminderModel({
    required this.id,
    required this.medicineName,
    this.dosageNote,
    required this.time,
    required this.repeatDaily,
  });

  ReminderModel copyWith({
    int? id,
    String? medicineName,
    String? dosageNote,
    DateTime? time,
    bool? repeatDaily,
  }) {
    return ReminderModel(
      id: id ?? this.id,
      medicineName: medicineName ?? this.medicineName,
      dosageNote: dosageNote ?? this.dosageNote,
      time: time ?? this.time,
      repeatDaily: repeatDaily ?? this.repeatDaily,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'medicine_name': medicineName,
      'dosage_note': dosageNote,
      'time': time.toIso8601String(),
      'repeat_daily': repeatDaily,
    };
  }

  factory ReminderModel.fromMap(Map<String, dynamic> map) {
    return ReminderModel(
      id: map['id'] as int,
      medicineName: map['medicine_name'] as String,
      dosageNote: map['dosage_note'] as String?,
      time: DateTime.parse(map['time'] as String),
      repeatDaily: map['repeat_daily'] as bool? ?? false,
    );
  }
}

/// ReminderService — local CRUD backed by flutter_secure_storage (medication
/// names/dosages are health data; legacy plaintext shared_preferences values
/// are migrated on first read and then removed).
/// Every mutation reschedules/cancels the OS notification.
class ReminderService {
  ReminderService._();
  static final ReminderService instance = ReminderService._();

  static const _key = 'reminders_list';
  final FlutterSecureStorage _secureStorage = appSecureStorage;

  Future<List<ReminderModel>> getAll() async {
    String? raw = await _secureStorage.read(key: _key);
    if (raw == null) {
      final prefs = await SharedPreferences.getInstance();
      raw = prefs.getString(_key);
      if (raw != null) {
        await _secureStorage.write(key: _key, value: raw);
        await prefs.remove(_key);
      }
    }
    if (raw == null) return [];
    final list = jsonDecode(raw) as List<dynamic>;
    return list
        .map((e) => ReminderModel.fromMap(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> _saveAll(List<ReminderModel> reminders) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key); // never keep a plaintext copy
    await _secureStorage.write(
        key: _key, value: jsonEncode(reminders.map((e) => e.toMap()).toList()));
  }

  /// Removes all locally stored reminders and cancels their notifications (logout).
  Future<void> clearLocalData() async {
    try {
      for (final r in await getAll()) {
        await NotificationService.instance.cancelReminder(r.id);
      }
    } catch (_) {}
    await _secureStorage.delete(key: _key);
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }

  Future<ReminderModel> add(ReminderModel reminder) async {
    final all = await getAll();
    all.add(reminder);
    await _saveAll(all);
    await _scheduleNotification(reminder);
    return reminder;
  }

  Future<ReminderModel> update(ReminderModel reminder) async {
    final all = await getAll();
    final idx = all.indexWhere((r) => r.id == reminder.id);
    if (idx != -1) all[idx] = reminder;
    await _saveAll(all);
    await NotificationService.instance.cancelReminder(reminder.id);
    await _scheduleNotification(reminder);
    return reminder;
  }

  Future<void> delete(int id) async {
    final all = await getAll();
    all.removeWhere((r) => r.id == id);
    await _saveAll(all);
    await NotificationService.instance.cancelReminder(id);
  }

  Future<void> _scheduleNotification(ReminderModel reminder) async {
    final now = DateTime.now();
    var scheduled = DateTime(
      now.year,
      now.month,
      now.day,
      reminder.time.hour,
      reminder.time.minute,
    );
    if (scheduled.isBefore(now)) {
      scheduled = scheduled.add(const Duration(days: 1));
    }
    await NotificationService.instance.scheduleReminder(
      reminder.id,
      'Medicine Reminder: ${reminder.medicineName}',
      reminder.dosageNote ?? 'Time to take your medicine',
      scheduled,
    );
  }
}
