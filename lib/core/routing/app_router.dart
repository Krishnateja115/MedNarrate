import 'package:go_router/go_router.dart';

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

  static final router = GoRouter(
    initialLocation: Routes.splash,
    routes: [
      GoRoute(
        path: Routes.splash,
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: Routes.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: Routes.signup,
        builder: (context, state) => const SignupScreen(),
      ),
      GoRoute(
        path: Routes.forgotPassword,
        builder: (context, state) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: Routes.onboarding,
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: Routes.dashboard,
        builder: (context, state) => const DashboardScreen(),
      ),
      GoRoute(
        path: Routes.reports,
        builder: (context, state) => const ReportsScreen(),
      ),
      GoRoute(
        path: Routes.upload,
        builder: (context, state) => const UploadScreen(),
      ),
      GoRoute(
        path: Routes.insights,
        builder: (context, state) => const InsightsScreen(),
      ),
      GoRoute(
        path: Routes.profile,
        builder: (context, state) => const ProfileScreen(),
      ),
      GoRoute(
        path: Routes.medicalProfile,
        builder: (context, state) => const MedicalProfileScreen(),
      ),
      GoRoute(
        path: Routes.emergencyContact,
        builder: (context, state) => const EmergencyContactScreen(),
      ),
      GoRoute(
        path: Routes.aiChat,
        builder: (context, state) {
          final reportId = state.extra as String?;
          return AIChatScreen(reportId: reportId);
        },
      ),
      GoRoute(
        path: Routes.reminders,
        builder: (context, state) => const ReminderScreen(),
      ),
      GoRoute(
        path: Routes.settings,
        builder: (context, state) => const SettingsScreen(),
      ),
      GoRoute(
        path: Routes.reportDetails,
        builder: (context, state) {
          final reportId = state.extra as String;
          return ReportDetailsScreen(reportId: reportId);
        },
      ),
      GoRoute(
        path: Routes.reportAnalysis,
        builder: (context, state) {
          final reportId = state.extra as String;
          return ReportAnalysisScreen(reportId: reportId);
        },
      ),
      GoRoute(
        path: Routes.reportTimeline,
        builder: (context, state) {
          final reportId = state.extra as String;
          return ReportTimelineScreen(reportId: reportId);
        },
      ),
    ],
  );
}