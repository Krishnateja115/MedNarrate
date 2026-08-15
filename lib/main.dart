import 'package:flutter/material.dart';

import 'core/routing/app_router.dart';
import 'core/services/notification_service.dart';
import 'core/services/storage_service.dart';
import 'core/services/biometric_service.dart';
import 'core/services/cache_service.dart';
import 'core/theme/app_theme.dart';

final themeModeNotifier = ValueNotifier<ThemeMode>(ThemeMode.system);

class AppLifecycleObserver extends WidgetsBindingObserver {
  DateTime? _backgroundedAt;

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) async {
    super.didChangeAppLifecycleState(state);

    if (state == AppLifecycleState.paused) {
      _backgroundedAt = DateTime.now();
    } else if (state == AppLifecycleState.resumed) {
      if (_backgroundedAt != null) {
        final diff = DateTime.now().difference(_backgroundedAt!);
        if (diff.inSeconds > 30) {
          final isEnabled = await BiometricService.instance.isBiometricEnabled();
          if (isEnabled) {
            AppRouter.router.push('/app-lock');
          }
        }
      }
      _backgroundedAt = null;
    }
  }
}


Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  WidgetsBinding.instance.addObserver(AppLifecycleObserver());
  await NotificationService.instance.initialize();
  await CacheService.instance.initialize();
  
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
        return MaterialApp.router(
          debugShowCheckedModeBanner: false,
          title: 'MedNarrate',
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: themeMode,
          routerConfig: AppRouter.router,
        );
      },
    );
  }
}