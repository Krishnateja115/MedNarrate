import 'biometric_service.dart';

Future<BiometricAvailability> checkWebAuthnAvailability() async {
  return BiometricAvailability.unsupported;
}

Future<BiometricResult> authenticateWebAuthn(String reason) async {
  return BiometricResult.unsupported;
}

Future<BiometricResult> verifyCurrentBiometricWebAuthn() async {
  return BiometricResult.unsupported;
}

Future<({BiometricResult status, String? credId})> registerNewCredentialWebAuthn() async {
  return (status: BiometricResult.unsupported, credId: null);
}

Future<BiometricResult> verifyNewCredentialWebAuthn(String credId) async {
  return BiometricResult.unsupported;
}

Future<bool> saveNewCredentialWebAuthn(String credId) async {
  return false;
}

Future<BiometricResult> disableBiometricWebAuthn() async {
  return BiometricResult.unsupported;
}

Future<bool> openWindowsSettingsWeb() async {
  return false;
}
