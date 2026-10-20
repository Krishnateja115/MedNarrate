import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/features/dashboard/widgets/announcement_banner.dart';
import 'package:mednarrate/features/dashboard/widgets/maintenance_banner.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('maintenance notice appears and clears after the next refresh',
      (tester) async {
    var enabled = true;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: MaintenanceBanner(loadStatus: () async => {
          'is_enabled': enabled,
          'scope': 'all',
          'message': 'Scheduled maintenance',
        }),
      ),
    ));
    await tester.pump();
    expect(find.text('Scheduled maintenance'), findsOneWidget);

    enabled = false;
    await tester.pump(const Duration(seconds: 15));
    await tester.pump();
    expect(find.text('Scheduled maintenance'), findsNothing);
  });

  testWidgets('announcement appears while the dashboard is open',
      (tester) async {
    SharedPreferences.setMockInitialValues({'preferred_language': 'hi'});
    var announcements = <Map<String, dynamic>>[];
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: AnnouncementBanner(
          role: 'patient',
          loadAnnouncements: (audience, language) async => announcements,
        ),
      ),
    ));
    await tester.pump();
    expect(find.text('New service notice'), findsNothing);

    announcements = [
      {'id': 'fresh-announcement', 'title': 'New service notice', 'message': 'Available now'},
    ];
    await tester.pump(const Duration(seconds: 30));
    await tester.pump();
    expect(find.text('New service notice'), findsOneWidget);
    expect(find.text('Available now'), findsOneWidget);
  });
}
