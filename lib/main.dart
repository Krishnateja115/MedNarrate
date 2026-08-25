import 'package:flutter/material.dart';
import 'package:timezone/data/latest.dart' as tz;

import 'core/routing/app_router.dart';
import 'core/services/notification_service.dart';
import 'core/services/storage_service.dart';
import 'core/services/biometric_service.dart';
import 'core/services/cache_service.dart';
import 'core/theme/app_theme.dart';

import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

final themeModeNotifier = ValueNotifier<ThemeMode>(ThemeMode.system);
final localeModeNotifier = ValueNotifier<Locale>(const Locale('en'));

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
  tz.initializeTimeZones();
  WidgetsBinding.instance.addObserver(AppLifecycleObserver());
  await NotificationService.instance.initialize();
  await CacheService.instance.initialize();
  
  // Load saved theme mode
  final savedThemeMode = await StorageService.instance.getThemeMode();
  themeModeNotifier.value = savedThemeMode;

  // Load saved language
  final savedLanguage = await StorageService.instance.getPreferredLanguage();
  localeModeNotifier.value = Locale(savedLanguage);

  runApp(const MedNarrateApp());
}

class MedNarrateApp extends StatelessWidget {
  const MedNarrateApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: themeModeNotifier,
      builder: (context, themeMode, _) {
        return ValueListenableBuilder<Locale>(
          valueListenable: localeModeNotifier,
          builder: (context, locale, _) {
            return MaterialApp.router(
              debugShowCheckedModeBanner: false,
              title: AppLocalizations.of(context)!.appTitle,
              theme: AppTheme.lightTheme,
              darkTheme: AppTheme.darkTheme,
              themeMode: themeMode,
              locale: locale,
              localizationsDelegates: const [
                AppLocalizations.delegate,
                GlobalMaterialLocalizations.delegate,
                GlobalWidgetsLocalizations.delegate,
                GlobalCupertinoLocalizations.delegate,
              ],
              supportedLocales: AppLocalizations.supportedLocales,
              routerConfig: AppRouter.router,
            );
          },
        );
      },
    );
  }
}