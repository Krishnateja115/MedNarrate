import 'package:local_auth/local_auth.dart';
import 'package:flutter/services.dart';
import 'storage_service.dart';

enum BiometricResult {
  success,
  failure,
  notAvailable,
  permanentlyDenied,
  error
}

class BiometricService {
  BiometricService._();
  static final BiometricService instance = BiometricService._();

  final LocalAuthentication _auth = LocalAuthentication();

  Future<bool> isAvailable() async {
    try {
      final isSupported = await _auth.isDeviceSupported();
      if (!isSupported) return false;
      final availableBiometrics = await _auth.getAvailableBiometrics();
      return availableBiometrics.isNotEmpty;
    } catch (e) {
      return false;
    }
  }

  Future<BiometricResult> authenticate() async {
    try {
      final didAuthenticate = await _auth.authenticate(
        localizedReason: 'Authenticate to access your medical records',
      );

      return didAuthenticate ? BiometricResult.success : BiometricResult.failure;
    } on PlatformException catch (e) {
      if (e.code == 'PasscodeNotSet') {
        return BiometricResult.error;
      } else if (e.code == 'NotEnrolled') {
        return BiometricResult.error;
      } else if (e.code == 'LockedOut' || e.code == 'PermanentlyLockedOut') {
        return BiometricResult.permanentlyDenied;
      }
      return BiometricResult.error;
    } catch (e) {
      return BiometricResult.error;
    }
  }

  Future<bool> isBiometricEnabled() async {
    return await StorageService.instance.getBiometricEnabled();
  }

  Future<bool> setBiometricEnabled(bool enabled) async {
    if (enabled) {
      final result = await authenticate();
      if (result == BiometricResult.success) {
        await StorageService.instance.setBiometricEnabled(true);
        return true;
      }
      return false;
    } else {
      await StorageService.instance.setBiometricEnabled(false);
      return true;
    }
  }
}
