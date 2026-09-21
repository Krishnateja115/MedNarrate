import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/config/app_config.dart';

void main() {
  group('AppConfig HTTPS Enforcement', () {
    test('production + http://example.com -> rejected', () {
      expect(
        () => AppConfig.validateApiBaseUrl('production', 'http://example.com'),
        throwsA(isA<StateError>()),
      );
    });

    test('production + https://example.com -> accepted', () {
      expect(
        AppConfig.validateApiBaseUrl('production', 'https://example.com'),
        equals('https://example.com'),
      );
    });

    test('development + http://localhost:8000 -> accepted', () {
      expect(
        AppConfig.validateApiBaseUrl('development', 'http://localhost:8000'),
        equals('http://localhost:8000'),
      );
    });

    test('development + http://10.0.2.2:8000 -> accepted', () {
      expect(
        AppConfig.validateApiBaseUrl('development', 'http://10.0.2.2:8000'),
        equals('http://10.0.2.2:8000'),
      );
    });
  });
}
