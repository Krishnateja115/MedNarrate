import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/services/biometric_service.dart';

void main() {
  group('BiometricResult enum', () {
    test('has all expected values', () {
      expect(BiometricResult.values, contains(BiometricResult.success));
      expect(BiometricResult.values, contains(BiometricResult.failure));
      expect(BiometricResult.values, contains(BiometricResult.notAvailable));
      expect(BiometricResult.values, contains(BiometricResult.permanentlyDenied));
      expect(BiometricResult.values, contains(BiometricResult.error));
    });

    test('success is not failure', () {
      expect(BiometricResult.success, isNot(BiometricResult.failure));
    });

    test('error is not success', () {
      expect(BiometricResult.error, isNot(BiometricResult.success));
    });
  });

  group('BiometricService singleton', () {
    test('instance is a singleton', () {
      final a = BiometricService.instance;
      final b = BiometricService.instance;
      expect(identical(a, b), isTrue);
    });

    test('instance is of type BiometricService', () {
      expect(BiometricService.instance, isA<BiometricService>());
    });
  });
}
