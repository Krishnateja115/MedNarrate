import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mednarrate/core/routing/app_router.dart';
import 'package:mednarrate/core/routing/routes.dart';
import 'package:mednarrate/features/auth/screens/login_screen.dart';
import 'package:mednarrate/features/auth/screens/signup_screen.dart';
import 'package:mednarrate/main.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('native app opens auth screens and validates the login form',
      (tester) async {
    await tester.pumpWidget(const MedNarrateApp());
    AppRouter.router.go(Routes.login);
    await tester.pumpAndSettle();

    expect(find.byType(LoginScreen), findsOneWidget);
    await tester.tap(find.text('Login'));
    await tester.pumpAndSettle();
    expect(find.text('Email is required'), findsOneWidget);
    expect(find.text('Password is required'), findsOneWidget);

    await tester.tap(find.text('Sign Up'));
    await tester.pumpAndSettle();
    expect(find.byType(SignupScreen), findsOneWidget);

    await tester.tap(find.text('Privacy Policy'));
    await tester.pumpAndSettle();
    expect(find.text('1. Overview & Data Transparency'), findsOneWidget);
  });
}
