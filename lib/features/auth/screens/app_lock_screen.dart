import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/routing/routes.dart';
import '../../../core/services/biometric_service.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/storage_service.dart';
import 'dart:async';
import 'package:mednarrate/l10n/app_localizations.dart';

class AppLockScreen extends StatefulWidget {
  const AppLockScreen({super.key});

  @override
  State<AppLockScreen> createState() => _AppLockScreenState();
}

class _AppLockScreenState extends State<AppLockScreen> {
  bool _isAuthenticating = false;
  String? _error;
  int _failures = 0;
  bool _lockedOut = false;
  int _lockoutSeconds = 30;
  Timer? _lockoutTimer;

  @override
  void initState() {
    super.initState();
    _authenticate();
  }

  @override
  void dispose() {
    _lockoutTimer?.cancel();
    super.dispose();
  }

  Future<void> _authenticate() async {
    if (_isAuthenticating || _lockedOut) return;

    setState(() {
      _isAuthenticating = true;
      _error = null;
    });

    final result = await BiometricService.instance.authenticate();

    if (!mounted) return;

    if (result == BiometricResult.success) {
      if (context.canPop()) {
        context.pop();
      } else {
        context.go(Routes.dashboard);
      }
    } else {
      setState(() {
        _failures++;
        if (_failures >= 3) {
          _lockout();
        } else {
          _error = 'Authentication failed. Please try again.';
        }
        _isAuthenticating = false;
      });
    }
  }

  void _lockout() {
    setState(() {
      _lockedOut = true;
      _lockoutSeconds = 30;
      _error = 'Too many attempts. Please try again in 30 seconds.';
    });
    
    _lockoutTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) return;
      setState(() {
        if (_lockoutSeconds > 1) {
          _lockoutSeconds--;
          _error = 'Too many attempts. Please try again in $_lockoutSeconds seconds.';
        } else {
          _lockedOut = false;
          _failures = 0;
          _error = null;
          timer.cancel();
        }
      });
    });
  }

  Future<void> _logout() async {
    try {
      await ApiService.instance.logout();
    } catch (_) {}
    await StorageService.instance.clearTokens();
    if (mounted) {
      context.go(Routes.login);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0C0C0E),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(AppLocalizations.of(context)!.appTitle,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                ),
              ),
              const SizedBox(height: 48),
              Icon(
                Icons.lock_outline,
                size: 80,
                color: AppColors.accentTeal,
              ),
              const SizedBox(height: 24),
              const Text(
                'Your records are locked',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 22,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Authenticate to continue',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.7),
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 48),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 24.0),
                  child: Text(
                    _error!,
                    style: TextStyle(
                      color: Colors.red.shade300,
                      fontSize: 14,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              ElevatedButton(
                onPressed: _lockedOut ? null : _authenticate,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: 8,
                  shadowColor: AppColors.primary.withValues(alpha: 0.5),
                ),
                child: _isAuthenticating
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Text(
                        'Unlock with Biometrics',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
              ),
              const SizedBox(height: 32),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Forgot? ',
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.5)),
                  ),
                  GestureDetector(
                    onTap: _logout,
                    child: Text(
                      'Log out',
                      style: TextStyle(
                        color: AppColors.accentTeal,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
