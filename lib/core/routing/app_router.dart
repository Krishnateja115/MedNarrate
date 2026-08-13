import 'package:flutter/material.dart';

import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/signup_screen.dart';
import '../../features/auth/screens/forgot_password_screen.dart';
import '../../features/auth/screens/onboarding_screen.dart';
import '../../features/auth/screens/splash_screen.dart';
import '../../features/dashboard/screens/dashboard_screen.dart';
import '../../features/reports/screens/reports_screen.dart';
import '../../features/reports/screens/upload_screen.dart';
import '../../features/reports/screens/report_details_screen.dart';
import '../../features/reports/screens/report_analysis_screen.dart';
import '../../features/reports/screens/report_timeline_screen.dart';
import '../../features/ai_chat/screens/ai_chat_screen.dart';
import '../../features/insights/screens/insights_screen.dart';
import '../../features/profile/screens/profile_screen.dart';
import '../../features/profile/screens/medical_profile_screen.dart';
import '../../features/profile/screens/emergency_contact_screen.dart';
import '../../features/reminders/screens/reminder_screen.dart';
import '../../features/settings/screens/settings_screen.dart';
import 'routes.dart';

class AppRouter {
  AppRouter._();

  static Route<dynamic> generateRoute(RouteSettings settings) {
    final args = settings.arguments;

    switch (settings.name) {
      case Routes.splash:
        return MaterialPageRoute(builder: (_) => const SplashScreen());

      case Routes.login:
        return MaterialPageRoute(builder: (_) => const LoginScreen());

      case Routes.signup:
        return MaterialPageRoute(builder: (_) => const SignupScreen());

      case Routes.forgotPassword:
        return MaterialPageRoute(builder: (_) => const ForgotPasswordScreen());

      case '/onboarding':
        return MaterialPageRoute(builder: (_) => const OnboardingScreen());

      case Routes.dashboard:
        return MaterialPageRoute(builder: (_) => const DashboardScreen());

      case Routes.reports:
        return MaterialPageRoute(builder: (_) => const ReportsScreen());

      case Routes.upload:
        return MaterialPageRoute(builder: (_) => const UploadScreen());

      case Routes.insights:
        return MaterialPageRoute(builder: (_) => const InsightsScreen());

      case Routes.profile:
        return MaterialPageRoute(builder: (_) => const ProfileScreen());

      case Routes.medicalProfile:
        return MaterialPageRoute(builder: (_) => const MedicalProfileScreen());

      case Routes.emergencyContact:
        return MaterialPageRoute(builder: (_) => const EmergencyContactScreen());

      case Routes.aiChat:
        final reportId = args is String ? args : null;
        return MaterialPageRoute(
          builder: (_) => AIChatScreen(reportId: reportId),
        );

      case Routes.reminders:
        return MaterialPageRoute(builder: (_) => const ReminderScreen());

      case Routes.settings:
        return MaterialPageRoute(builder: (_) => const SettingsScreen());

      case '/report-details':
        final reportId = args as String;
        return MaterialPageRoute(
          builder: (_) => ReportDetailsScreen(reportId: reportId),
        );

      case '/report-analysis':
        final reportId = args as String;
        return MaterialPageRoute(
          builder: (_) => ReportAnalysisScreen(reportId: reportId),
        );

      case '/report-timeline':
        final reportId = args as String;
        return MaterialPageRoute(
          builder: (_) => ReportTimelineScreen(reportId: reportId),
        );

      default:
        return MaterialPageRoute(
          builder: (_) => const Scaffold(
            body: Center(child: Text('Page not found')),
          ),
        );
    }
  }
}