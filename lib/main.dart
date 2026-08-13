import 'package:flutter/material.dart';

import 'core/routing/app_router.dart';
import 'core/routing/routes.dart';
import 'core/services/notification_service.dart';
import 'core/services/storage_service.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/screens/splash_screen.dart';

final themeModeNotifier = ValueNotifier<ThemeMode>(ThemeMode.system);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService.instance.init();
  
  // Load saved theme mode
  final savedThemeMode = await StorageService.instance.getThemeMode();
  themeModeNotifier.value = savedThemeMode;

  runApp(const MedNarrateApp());
}

class MedNarrateApp extends StatelessWidget {
  const MedNarrateApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: themeModeNotifier,
      builder: (context, themeMode, _) {
        return MaterialApp(
          debugShowCheckedModeBanner: false,
          title: 'MedNarrate',
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: themeMode,
          onGenerateRoute: AppRouter.generateRoute,
          initialRoute: Routes.splash,
          home: const SplashScreen(),
        );
      },
    );
  }
}