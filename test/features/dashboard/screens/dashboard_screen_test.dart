import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mocktail/mocktail.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:mednarrate/features/dashboard/screens/dashboard_screen.dart';
import 'package:mednarrate/core/services/api_service.dart';
import 'package:mednarrate/core/services/api_models.dart';
import 'package:mednarrate/core/routing/routes.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class MockApiService extends Mock implements ApiService {}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('DashboardScreen - Add Medicine navigates to reminders', (WidgetTester tester) async {
    final mockApi = MockApiService();
    when(() => mockApi.getMe()).thenAnswer((_) async => const UserModel(
      id: '1', 
      email: 'test@test.com', 
      fullName: 'Test User', 
      role: 'patient',
      preferredLanguage: 'en',
      isActive: true,
    ));
    when(() => mockApi.listReports()).thenAnswer((_) async => []);
    when(() => mockApi.getMedicationSchedules()).thenAnswer((_) async => []);
    
    ApiService.instance = mockApi;

    String? pushedRoute;
    Object? pushedExtra;

    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const DashboardScreen(),
        ),
        GoRoute(
          path: Routes.reminders,
          builder: (context, state) {
            pushedRoute = Routes.reminders;
            pushedExtra = state.extra;
            return const Scaffold(body: Text('Reminders'));
          },
        ),
        GoRoute(
          path: Routes.upload,
          builder: (context, state) {
            pushedRoute = Routes.upload;
            return const Scaffold(body: Text('Upload'));
          },
        ),
      ],
    );

    await tester.pumpWidget(MaterialApp.router(
      routerConfig: router,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
    ));
    await tester.pumpAndSettle();

    // Verify Add Medicine tap
    final addIcon = find.byIcon(Icons.add_circle_outline_rounded);
    await tester.ensureVisible(addIcon);
    await tester.pumpAndSettle();
    expect(addIcon, findsOneWidget);
    
    await tester.tap(addIcon);
    await tester.pumpAndSettle();
    
    expect(pushedRoute, Routes.reminders, reason: 'Tapping Add Medicine MUST push to Routes.reminders');
    expect(pushedExtra, isA<Map<String, dynamic>>());
    expect((pushedExtra as Map<String, dynamic>)['autoOpenAdd'], isTrue);
  });

  testWidgets('DashboardScreen - Confirm to Schedule navigates to reminders with prefill', (WidgetTester tester) async {
    final mockApi = MockApiService();
    when(() => mockApi.getMe()).thenAnswer((_) async => const UserModel(
      id: '1', 
      email: 'test@test.com', 
      fullName: 'Test User', 
      role: 'patient',
      preferredLanguage: 'en',
      isActive: true,
    ));
    when(() => mockApi.listReports()).thenAnswer((_) async => []);
    
    // Add a reported medication to trigger the "Confirm to Schedule" UI
    final sampleMed = {
      'id': 'med1', 
      'medication_name': 'Aspirin',
      'dosage': '81mg',
    };
    when(() => mockApi.getMedicationSchedules()).thenAnswer((_) async => [sampleMed]);
    
    ApiService.instance = mockApi;

    String? pushedRoute;
    Object? pushedExtra;

    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const DashboardScreen(),
        ),
        GoRoute(
          path: Routes.reminders,
          builder: (context, state) {
            pushedRoute = Routes.reminders;
            pushedExtra = state.extra;
            return const Scaffold(body: Text('Reminders'));
          },
        ),
        GoRoute(
          path: Routes.upload,
          builder: (context, state) {
            pushedRoute = Routes.upload;
            return const Scaffold(body: Text('Upload'));
          },
        ),
      ],
    );

    await tester.pumpWidget(MaterialApp.router(
      routerConfig: router,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
    ));
    await tester.pumpAndSettle();

    // The widget shows "Confirm to Schedule" or an arrow button for reported meds.
    // Let's tap the button which could be an icon (Icons.add or Icons.arrow_forward_ios) or text.
    // Usually it's "Confirm to Schedule" or similar, but the easiest is finding the InkWell or button.
    // The previous test failed to find 'Confirm'. Let's check MedicineReminderCard to see what to find.
    // A safe bet is finding the exact widget. Let's just tap the first element that's tapable inside the reported medication list or the string 'Aspirin'.
    final confirmIcon = find.byIcon(Icons.check_circle_outline);
    await tester.ensureVisible(confirmIcon);
    await tester.pumpAndSettle();
    expect(confirmIcon, findsOneWidget);
    
    await tester.tap(confirmIcon);
    await tester.pumpAndSettle();

    expect(pushedRoute, Routes.reminders, reason: 'Tapping confirm MUST push to Routes.reminders');
    expect(pushedExtra, isA<Map<String, dynamic>>());
    expect((pushedExtra as Map<String, dynamic>)['prefillMed'], equals(sampleMed));
  });
}
