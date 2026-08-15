import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/material.dart';
import 'storage_service.dart';
import 'api_service.dart';
import 'package:flutter/foundation.dart';

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  NotificationService.instance.showLocalNotification(
    message.notification?.title ?? 'Notification',
    message.notification?.body ?? '',
  );
}

class NotificationService {
  NotificationService._();
  static final NotificationService instance = NotificationService._();

  final FlutterLocalNotificationsPlugin _localNotificationsPlugin =
      FlutterLocalNotificationsPlugin();

  bool _initialized = false;
  final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

  Future<void> initialize() async {
    if (_initialized) return;

    try {
      await Firebase.initializeApp();
      
      // Request permissions
      NotificationSettings settings = await FirebaseMessaging.instance.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );

      if (settings.authorizationStatus == AuthorizationStatus.authorized) {
        // Init Local Notifications
        const AndroidInitializationSettings initializationSettingsAndroid =
            AndroidInitializationSettings('@mipmap/ic_launcher');
        const DarwinInitializationSettings initializationSettingsDarwin =
            DarwinInitializationSettings();
        const InitializationSettings initializationSettings = InitializationSettings(
          android: initializationSettingsAndroid,
          iOS: initializationSettingsDarwin,
        );
        
        await _localNotificationsPlugin.initialize(
          initializationSettings,
          onDidReceiveNotificationResponse: (details) {
            // Navigate to medications screen if tapped
            if (navigatorKey.currentState != null) {
              navigatorKey.currentState!.pushNamed('/medications');
            }
          },
        );

        // Get token
        String? token = await FirebaseMessaging.instance.getToken();
        if (token != null) {
          await _registerToken(token);
        }

        // Token refresh
        FirebaseMessaging.instance.onTokenRefresh.listen(_registerToken);

        // Setup message handlers
        _setupMessageHandlers();
        _initialized = true;
      }
    } catch (e) {
      debugPrint("Firebase init failed: $e");
    }
  }

  Future<void> _registerToken(String token) async {
    try {
      // await StorageService.instance.saveFCMToken(token);
      final platform = defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android';
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
      if (navigatorKey.currentState != null) {
        navigatorKey.currentState!.pushNamed('/medications');
      }
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
    const NotificationDetails platformChannelSpecifics =
        NotificationDetails(android: androidPlatformChannelSpecifics, iOS: DarwinNotificationDetails());
        
    await _localNotificationsPlugin.show(
      DateTime.now().millisecond,
      title,
      body,
      platformChannelSpecifics,
    );
  }

  Future<void> cancelReminder(int id) async {
    if (kIsWeb) return;
    try {
      await _localNotificationsPlugin.cancel(id);
    } catch (e) {
      debugPrint('cancelReminder failed: $e');
    }
  }

  Future<void> scheduleReminder(
    int id,
    String title,
    String body,
    DateTime scheduledDate,
  ) async {
    if (kIsWeb) return;
    try {
      await showLocalNotification(title, body);
    } catch (e) {
      debugPrint('scheduleReminder failed: $e');
    }
  }
}
