import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/notification_service.dart';

// NotificationService wraps Firebase Messaging + flutter_local_notifications,
// which need real platform channels to fully initialize. Rather than fake
// those channels (fragile, and not verifiable without a device), this covers
// the two guarantees the rest of the app actually depends on: it is a true
// singleton, and it exposes one stable navigator key that notification taps
// use to push routes onto the live app navigator.
void main() {
  test('NotificationService.instance is a single shared instance app-wide', () {
    expect(identical(NotificationService.instance, NotificationService.instance), isTrue);
  });

  test('navigatorKey is a stable GlobalKey<NavigatorState> reused across access', () {
    final key1 = NotificationService.instance.navigatorKey;
    final key2 = NotificationService.instance.navigatorKey;

    expect(key1, isA<GlobalKey<NavigatorState>>());
    expect(identical(key1, key2), isTrue,
        reason: 'notification taps navigate via this exact key, so it must never be recreated');
  });
}
