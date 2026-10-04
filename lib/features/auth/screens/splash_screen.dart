import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_strings.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/biometric_service.dart';
import '../../../core/services/storage_service.dart';
import '../../../core/routing/routes.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fade;
  late Animation<double> _scale;
  String? _startupError;
  String _startupErrorTitle = 'Unable to connect';

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );

    _fade = CurvedAnimation(parent: _controller, curve: Curves.easeIn);

    _scale = Tween<double>(begin: .85, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutBack),
    );

    _controller.forward();

    Timer(const Duration(seconds: 2), _checkAuthAndNavigate);
  }

  Future<void> _checkAuthAndNavigate() async {
    if (!mounted) return;

    String? token;
    try {
      token = await StorageService.instance.getAccessToken();
    } on SecureStorageUnavailableException {
      if (mounted) {
        setState(() {
          _startupErrorTitle = 'Secure sign-in is unavailable';
          _startupError =
              'MedNarrate cannot access the encrypted macOS Keychain. '
              'Quit the app, install the latest build, and then try again.';
        });
      }
      return;
    }
    if (token != null) {
      try {
        await ApiService.instance.getMe();
        if (!mounted) return;

        final isBioEnabled =
            await BiometricService.instance.isBiometricEnabled();
        if (!mounted) return;
        if (isBioEnabled) {
          context.go('/app-lock');
        } else {
          context.go(Routes.dashboard);
        }
        return;
      } catch (error) {
        if (error is ApiException && error.statusCode == 0) {
          if (mounted) setState(() => _startupError = error.message);
          return;
        }
        // Invalid or revoked credentials — fall through to login/onboarding.
        await StorageService.instance.clearTokens();
      }
    }

    if (!mounted) return;
    final seen = await StorageService.instance.isOnboardingSeen();
    if (!mounted) return;
    if (seen) {
      context.go(Routes.login);
    } else {
      context.go(Routes.onboarding);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_startupError != null) {
      return Scaffold(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.cloud_off_outlined, size: 56),
                const SizedBox(height: 16),
                Text(_startupErrorTitle,
                    style:
                        TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),
                Text(_startupError!, textAlign: TextAlign.center),
                const SizedBox(height: 22),
                ElevatedButton.icon(
                  onPressed: () => setState(() {
                    _startupError = null;
                    Timer(const Duration(milliseconds: 100),
                        _checkAuthAndNavigate);
                  }),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
      );
    }
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Center(
        child: FadeTransition(
          opacity: _fade,
          child: ScaleTransition(
            scale: _scale,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  height: 110,
                  width: 110,
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: Icon(
                    Icons.medical_services_rounded,
                    size: 60,
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
                ),
                SizedBox(height: 28),
                Text(
                  AppStrings.appName,
                  style: TextStyle(
                    fontSize: 34,
                    fontWeight: FontWeight.w700,
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  AppStrings.appTagline,
                  style: TextStyle(
                    fontSize: 16,
                    color: AppColors.textSecondary,
                  ),
                ),
                SizedBox(height: 50),
                SizedBox(
                  width: 28,
                  height: 28,
                  child: CircularProgressIndicator(strokeWidth: 3),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
