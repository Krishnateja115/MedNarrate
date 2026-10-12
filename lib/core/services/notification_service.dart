import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/material.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'api_service.dart';
import 'package:flutter/foundation.dart';
import 'package:timezone/timezone.dart' as tz;

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

class NotificationService {
  NotificationService._();
  static final NotificationService instance = NotificationService._();

  final FlutterLocalNotificationsPlugin _localNotificationsPlugin =
      FlutterLocalNotificationsPlugin();

  bool _initialized = false;
  bool _notificationsAllowed = false;
  bool _exactAlarmsAllowed = false;
  bool _exactPermissionChecked = false;
  bool get notificationsAllowed => _notificationsAllowed;
  VoidCallback? onOpenMedications;

  void _openMedications() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      onOpenMedications?.call();
    });
  }

  Future<void> initialize() async {
    if (_initialized) return;
    if (kIsWeb) {
      _initialized = true;
      return;
    }

    // Local medicine alarms must work even when Firebase is unavailable.
    try {
      const initializationSettings = InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(),
      );
      await _localNotificationsPlugin.initialize(
        initializationSettings,
        onDidReceiveNotificationResponse: (details) {
          _openMedications();
        },
      );
      await refreshPermissions();
      await refreshTimezone();
    } catch (error) {
      _notificationsAllowed = false;
      debugPrint('Local notification setup failed: $error');
    }
    _initialized = true;

    try {
      await Firebase.initializeApp();

      NotificationSettings settings =
          await FirebaseMessaging.instance.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );

      if (settings.authorizationStatus == AuthorizationStatus.authorized) {
        // Get token
        String? token = await FirebaseMessaging.instance.getToken();
        if (token != null) {
          await _registerToken(token);
        }

        // Token refresh
        FirebaseMessaging.instance.onTokenRefresh.listen(_registerToken);

        // Setup message handlers
        _setupMessageHandlers();
        if (await FirebaseMessaging.instance.getInitialMessage() != null) {
          _openMedications();
        }
      }
    } catch (e) {
      debugPrint("Firebase init failed: $e");
    }
  }

  Future<void> refreshTimezone() async {
    if (kIsWeb) return;
    final localTimezone = await FlutterTimezone.getLocalTimezone();
    tz.setLocalLocation(tz.getLocation(localTimezone.identifier));
  }

  Future<void> refreshPermissions() async {
    if (kIsWeb) return;
    if (defaultTargetPlatform == TargetPlatform.android) {
      final android =
          _localNotificationsPlugin.resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>();
      _notificationsAllowed =
          await android?.requestNotificationsPermission() ?? false;
    } else {
      _notificationsAllowed = true;
    }
  }

  Future<void> _registerToken(String token) async {
    try {
      // await StorageService.instance.saveFCMToken(token);
      final platform =
          defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android';
      await ApiService.instance.registerPushToken(token, platform);
    } catch (e) {
      debugPrint("Failed to register token: $e");
    }
  }

  void _setupMessageHandlers() {
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      showLocalNotification(
        message.notification?.title ?? 'Notification',
        message.notification?.body ?? '',
      );
    });

    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      _openMedications();
    });
  }

  Future<void> showLocalNotification(String title, String body) async {
    if (kIsWeb) return; // not supported on web
    const AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
      'mednarrate_reminders',
      'Medication Reminders',
      importance: Importance.max,
      priority: Priority.high,
      showWhen: false,
    );
    const NotificationDetails platformChannelSpecifics = NotificationDetails(
        android: androidPlatformChannelSpecifics,
        iOS: DarwinNotificationDetails());

    await _localNotificationsPlugin.show(
      DateTime.now().millisecond,
      title,
      body,
      platformChannelSpecifics,
    );
  }

  Future<void> cancelReminder(int id) async {
    if (kIsWeb) return;
    await _localNotificationsPlugin.cancel(id);
  }

  Future<void> scheduleDailyReminder(
    int id,
    String title,
    String body,
    DateTime nextOccurrence, {
    bool repeatDaily = true,
  }) async {
    if (kIsWeb || !_notificationsAllowed) return;
    if (defaultTargetPlatform == TargetPlatform.android &&
        !_exactPermissionChecked) {
      _exactPermissionChecked = true;
      final android =
          _localNotificationsPlugin.resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>();
      try {
        _exactAlarmsAllowed =
            await android?.requestExactAlarmsPermission() ?? false;
      } catch (error) {
        _exactAlarmsAllowed = false;
        debugPrint('Exact alarm permission unavailable: $error');
      }
    }
    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        'mednarrate_reminders',
        'Medication Reminders',
        importance: Importance.max,
        priority: Priority.high,
      ),
      iOS: DarwinNotificationDetails(),
    );
    Future<void> schedule(AndroidScheduleMode mode) =>
        _localNotificationsPlugin.zonedSchedule(
          id,
          title,
          body,
          tz.TZDateTime.from(nextOccurrence, tz.local),
          details,
          androidScheduleMode: mode,
          uiLocalNotificationDateInterpretation:
              UILocalNotificationDateInterpretation.absoluteTime,
          matchDateTimeComponents:
              repeatDaily ? DateTimeComponents.time : null,
        );
    if (_exactAlarmsAllowed) {
      try {
        await schedule(AndroidScheduleMode.exactAllowWhileIdle);
        return;
      } catch (error) {
        debugPrint('Exact alarm unavailable; using inexact timing: $error');
        _exactAlarmsAllowed = false;
      }
    }
    await schedule(AndroidScheduleMode.inexactAllowWhileIdle);
  }

  Future<void> scheduleReminder(
      int id, String title, String body, DateTime scheduledDate,
      {bool repeatDaily = false}) async {
    if (kIsWeb || !_notificationsAllowed) return;
    try {
      const AndroidNotificationDetails androidPlatformChannelSpecifics =
          AndroidNotificationDetails(
        'mednarrate_reminders',
        'Medication Reminders',
        importance: Importance.max,
        priority: Priority.high,
      );
      const NotificationDetails platformChannelSpecifics = NotificationDetails(
          android: androidPlatformChannelSpecifics,
          iOS: DarwinNotificationDetails());

      await _localNotificationsPlugin.zonedSchedule(
        id,
        title,
        body,
        tz.TZDateTime.from(scheduledDate, tz.local),
        platformChannelSpecifics,
        androidScheduleMode: _exactAlarmsAllowed
            ? AndroidScheduleMode.exactAllowWhileIdle
            : AndroidScheduleMode.inexactAllowWhileIdle,
        uiLocalNotificationDateInterpretation:
            UILocalNotificationDateInterpretation.absoluteTime,
        matchDateTimeComponents: repeatDaily ? DateTimeComponents.time : null,
      );
    } catch (e) {
      debugPrint('scheduleReminder failed: $e');
    }
  }
}
