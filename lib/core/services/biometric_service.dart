import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:local_auth/local_auth.dart';
import 'storage_service.dart';

enum BiometricAvailability {
  available,
  notConfigured,
  noPlatformAuthenticator,
  webUnsupported,
  unsupported,
}

enum BiometricResult {
  success,
  failure,
  notAvailable,
  notConfigured,
  cancelled,
  unsupported,
  permanentlyDenied,
  error,
}

class BiometricService {
  BiometricService._();
  static final BiometricService instance = BiometricService._();

  final LocalAuthentication _auth = LocalAuthentication();
  bool isUnlocked = false;

  Future<BiometricAvailability> checkAvailability() async {
    if (kIsWeb) {
      return BiometricAvailability.webUnsupported;
    } else {
      try {
        final isSupported = await _auth.isDeviceSupported();
        final canCheck = await _auth.canCheckBiometrics;
        if (!isSupported && !canCheck) {
          return BiometricAvailability.noPlatformAuthenticator;
        }

        final availableBiometrics = await _auth.getAvailableBiometrics();
        if (availableBiometrics.isEmpty) {
          return BiometricAvailability.notConfigured;
        }
        return BiometricAvailability.available;
      } catch (e) {
        return BiometricAvailability.unsupported;
      }
    }
  }

  Future<bool> isAvailable() async {
    final status = await checkAvailability();
    return status == BiometricAvailability.available;
  }

  Future<BiometricResult> authenticate({String reason = 'Authenticate to access your medical records'}) async {
    if (kIsWeb) {
      return BiometricResult.unsupported;
    }

    try {
      final didAuthenticate = await _auth.authenticate(
        localizedReason: reason,
      );

      final result = didAuthenticate ? BiometricResult.success : BiometricResult.failure;
      if (result == BiometricResult.success) {
        isUnlocked = true;
      }
      return result;
    } on PlatformException catch (e) {
      if (e.code == 'PasscodeNotSet' || e.code == 'NotEnrolled') {
        return BiometricResult.notConfigured;
      } else if (e.code == 'NotAvailable') {
        return BiometricResult.notAvailable;
      } else if (e.code == 'LockedOut' || e.code == 'PermanentlyLockedOut') {
        return BiometricResult.permanentlyDenied;
      }
      return BiometricResult.error;
    } catch (e) {
      return BiometricResult.error;
    }
  }

  Future<BiometricResult> verifyCurrentBiometric() async {
    return await authenticate(reason: 'Verify your current biometric to continue');
  }

  Future<bool> isBiometricEnabled() async {
    if (kIsWeb) return false;
    return await StorageService.instance.getBiometricEnabled();
  }

  Future<BiometricResult> setBiometricEnabled(bool enabled) async {
    if (enabled) {
      final result = await authenticate(reason: 'Authenticate using fingerprint or Face ID to enable Biometric App Lock');
      if (result == BiometricResult.success) {
        await StorageService.instance.setBiometricEnabled(true);
        isUnlocked = true;
      }
      return result;
    } else {
      final result = await authenticate(reason: 'Authenticate using fingerprint or Face ID to disable Biometric App Lock');
      if (result == BiometricResult.success) {
        await StorageService.instance.setBiometricEnabled(false);
        isUnlocked = true;
      }
      return result;
    }
  }
}
