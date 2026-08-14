import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tz;

/// NotificationService — wraps flutter_local_notifications.
/// Call [init] from main() before runApp.
class NotificationService {
  NotificationService._();
  static final NotificationService instance = NotificationService._();

  final _plugin = FlutterLocalNotificationsPlugin();

  Future<void> init() async {
    tz.initializeTimeZones();

    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const ios = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    const settings = InitializationSettings(android: android, iOS: ios, macOS: ios);
    await _plugin.initialize(settings);
  }

  Future<void> scheduleReminder(
      int id, String title, String body, DateTime time) async {
    final scheduledTime = tz.TZDateTime.from(time, tz.local);
    await _plugin.zonedSchedule(
      id,
      title,
      body,
      scheduledTime,
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'mednarrate_reminders',
          'Medicine Reminders',
          channelDescription: 'Reminders for medicines',
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: DarwinNotificationDetails(),
        macOS: DarwinNotificationDetails(),
      ),
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
    );
  }

  Future<void> cancelReminder(int id) => _plugin.cancel(id);

  Future<void> showInstantNotification(String title, String body) async {
    await _plugin.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'mednarrate_general',
          'General Notifications',
          channelDescription: 'App notifications',
          importance: Importance.defaultImportance,
        ),
        iOS: DarwinNotificationDetails(),
        macOS: DarwinNotificationDetails(),
      ),
    );
  }
}
