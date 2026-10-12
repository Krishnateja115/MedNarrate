import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/notification_service.dart';

// NotificationService wraps Firebase Messaging + flutter_local_notifications,
// which need real platform channels to fully initialize. Rather than fake
// those channels (fragile, and not verifiable without a device), this covers
// the singleton and the navigation callback used by notification taps.
void main() {
  test('NotificationService.instance is a single shared instance app-wide', () {
    expect(identical(NotificationService.instance, NotificationService.instance), isTrue);
  });

  testWidgets('notification tap invokes the configured router callback', (tester) async {
    var calls = 0;
    NotificationService.instance.onOpenMedications = () => calls++;

    NotificationService.instance.openMedications();
    await tester.pump();

    expect(calls, 1);
    NotificationService.instance.onOpenMedications = null;
  });
}
