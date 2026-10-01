import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/features/insights/screens/insights_screen.dart';
import 'package:mednarrate/l10n/app_localizations.dart';
import 'package:hive_flutter/hive_flutter.dart';

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    Hive.init('.');
  });

  testWidgets('InsightsScreen renders Hindi translations correctly', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('hi'),
        home: const InsightsScreen(),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    // Verify the translated strings are present
    expect(find.text('स्वास्थ्य अंतर्दृष्टि'), findsOneWidget); // healthInsights
  });
}
