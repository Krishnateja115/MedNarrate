import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// The encrypted storage configuration shared by all native MedNarrate data.
///
/// The standard macOS Keychain is encrypted and works for local ad-hoc builds
/// without requiring an Apple developer signing identity. Keeping one shared
/// configuration prevents a background service from silently using different
/// Keychain settings than the login service.
const appSecureStorage = FlutterSecureStorage(
  aOptions: AndroidOptions(),
  iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  mOptions: MacOsOptions(usesDataProtectionKeychain: false),
);
