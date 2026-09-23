import 'dart:io';
import 'package:flutter/material.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:file_picker/file_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';


import 'core/routing/app_router.dart';
import 'core/services/notification_service.dart';
import 'core/services/storage_service.dart';
import 'core/services/biometric_service.dart';
import 'core/services/cache_service.dart';
import 'core/theme/app_theme.dart';
import 'core/config/app_config.dart';

import 'package:mednarrate/l10n/app_localizations.dart';
import 'boot_screen.dart';

final themeModeNotifier = ValueNotifier<ThemeMode>(ThemeMode.system);
final localeModeNotifier = ValueNotifier<Locale>(const Locale('en'));

class AppLifecycleObserver extends WidgetsBindingObserver {
  DateTime? _backgroundedAt;

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) async {
    super.didChangeAppLifecycleState(state);

    if (state == AppLifecycleState.paused || state == AppLifecycleState.hidden || state == AppLifecycleState.inactive) {
      _backgroundedAt ??= DateTime.now();
    } else if (state == AppLifecycleState.resumed) {
      if (_backgroundedAt != null) {
        final diff = DateTime.now().difference(_backgroundedAt!);
        if (diff.inMinutes >= 3) {
          final isEnabled = await BiometricService.instance.isBiometricEnabled();
          if (isEnabled) {
            BiometricService.instance.isUnlocked = false;
            AppRouter.router.go('/app-lock');
          }
        }
      }
      _backgroundedAt = null;
    }
  }
}

Future<bool> _isBackendHealthy() async {
  try {
    final result = await HttpClient()
        .getUrl(Uri.parse('${AppConfig.apiBaseUrl}/health'))
        .then((req) => req.close())
        .timeout(const Duration(seconds: 2));
    return result.statusCode == 200;
  } catch (_) {
    return false;
  }
}

Future<String?> _resolveBackendPath() async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getString('macos_backend_path');
}

Future<void> _saveBackendPath(String path) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString('macos_backend_path', path);
}

Future<void> _ensureBackendRunningOnMacOS() async {
  if (!Platform.isMacOS) return;
  if (await _isBackendHealthy()) return;

  String? backendPath = await _resolveBackendPath();
  if (backendPath == null || !await Directory(backendPath).exists() || backendPath == '/') {
    String? selectedDirectory = await FilePicker.platform.getDirectoryPath(dialogTitle: 'Select mednarrate-backend folder');
    if (selectedDirectory != null) {
      await _saveBackendPath(selectedDirectory);
      backendPath = selectedDirectory;
    } else {
      throw Exception("Backend path not selected.");
    }
  }

  final venvPython = File('$backendPath/venv/bin/python3');
  final dotVenvPython = File('$backendPath/.venv/bin/python3');
  String pythonExe = '';

  if (await venvPython.exists()) {
    pythonExe = venvPython.path;
  } else if (await dotVenvPython.exists()) {
    pythonExe = dotVenvPython.path;
  } else {
    throw Exception("Missing virtual environment. Neither 'venv' nor '.venv' found in backend directory ($backendPath). Please create one and install requirements.");
  }

  await Process.start(
    '/bin/sh',
    ['-c', 'cd "$backendPath" && "$pythonExe" run_server.py > /tmp/mednarrate_backend.log 2>&1'],
    mode: ProcessStartMode.detached,
  );

  const maxWait = Duration(seconds: 20);
  final start = DateTime.now();
  while (DateTime.now().difference(start) < maxWait) {
    if (await _isBackendHealthy()) return;
    await Future.delayed(const Duration(milliseconds: 500));
  }
  throw Exception("Timeout waiting for local server to start on macOS.");
}

Future<void> _ensureBackendRunningOnWindows() async {
  if (!Platform.isWindows) return;
  if (await _isBackendHealthy()) return;

  final exeDir = File(Platform.resolvedExecutable).parent.path;
  final backendExe = '$exeDir\\backend\\mednarrate_backend.exe';

  if (!await File(backendExe).exists()) {
    throw Exception("Backend executable not found at $backendExe");
  }

  await Process.start(
    backendExe,
    [],
    mode: ProcessStartMode.detached,
    workingDirectory: '$exeDir\\backend',
  );

  const maxWait = Duration(seconds: 25);
  final start = DateTime.now();
  while (DateTime.now().difference(start) < maxWait) {
    if (await _isBackendHealthy()) return;
    await Future.delayed(const Duration(milliseconds: 500));
  }
  throw Exception("Timeout waiting for local server to start on Windows.");
}

Future<void> _runBootSequence() async {
  try {
    if (Platform.isMacOS) {
      await _ensureBackendRunningOnMacOS();
    } else if (Platform.isWindows) {
      await _ensureBackendRunningOnWindows();
    }
    
    // Proceed to app init
    WidgetsBinding.instance.addObserver(AppLifecycleObserver());
    await NotificationService.instance.initialize();
    await CacheService.instance.initialize();
    
    final savedThemeMode = await StorageService.instance.getThemeMode();
    themeModeNotifier.value = savedThemeMode;

    final savedLanguage = await StorageService.instance.getPreferredLanguage();
    localeModeNotifier.value = Locale(savedLanguage);

    runApp(const MedNarrateApp());
  } catch (e) {
    File('/tmp/mednarrate_debug.log').writeAsStringSync('BootError: ${e.toString()}\n', mode: FileMode.append);
    runApp(MaterialApp(
      debugShowCheckedModeBanner: false,
      home: BootErrorScreen(
        error: e.toString(),
        onRetry: () {
          File('/tmp/mednarrate_debug.log').writeAsStringSync('BootError: Retrying\n', mode: FileMode.append);
          runApp(const MaterialApp(debugShowCheckedModeBanner: false, home: BootScreen(status: 'Retrying connection...')));
          _runBootSequence();
        },
        onChangeBackend: Platform.isMacOS ? () async {
          final prefs = await SharedPreferences.getInstance();
          await prefs.remove('macos_backend_path');
          File('/tmp/mednarrate_debug.log').writeAsStringSync('BootError: Reset backend path\n', mode: FileMode.append);
          runApp(const MaterialApp(debugShowCheckedModeBanner: false, home: BootScreen(status: 'Retrying connection...')));
          _runBootSequence();
        } : null,
      ),
    ));
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  tz.initializeTimeZones();
  
  runApp(const MaterialApp(debugShowCheckedModeBanner: false, home: BootScreen(status: 'Starting local server...')));
  
  await _runBootSequence();
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
              onGenerateTitle: (context) => AppLocalizations.of(context)!.appTitle,
              theme: AppTheme.lightTheme,
              darkTheme: AppTheme.darkTheme,
              themeMode: themeMode,
              locale: locale,
              localizationsDelegates: AppLocalizations.localizationsDelegates,
              supportedLocales: AppLocalizations.supportedLocales,
              routerConfig: AppRouter.router,
            );
          },
        );
      },
    );
  }
}
