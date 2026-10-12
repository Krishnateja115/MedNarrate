import 'package:flutter/foundation.dart';

class AppConfig {
  static const bool isLocalDevMode = !kReleaseMode &&
      bool.fromEnvironment('LOCAL_DEV_MODE', defaultValue: kDebugMode);

  /// API_BASE_URL is always the backend origin (without /api/v1).
  static const String _rawApiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    // Local web builds must be usable with a normal `flutter run -d chrome`
    // command. Production builds still require an explicit HTTPS URL because
    // validateApiBaseUrl rejects this development default in production.
    defaultValue: 'http://127.0.0.1:8000',
  );
  
  static String get apiBaseUrl {
    var url = _rawApiBaseUrl.trim().replaceFirst(RegExp(r'/+$'), '');
    // Accept the old value temporarily, but expose only the origin to callers.
    if (url.endsWith('/api/v1')) url = url.substring(0, url.length - 7);
    if (defaultTargetPlatform == TargetPlatform.android &&
        isLocalDevMode &&
        url == 'http://127.0.0.1:8000') {
      return 'http://10.0.2.2:8000';
    }
    return validateApiBaseUrl(kReleaseMode ? 'production' : environment, url);
  }

  static String get apiRoot => '$apiBaseUrl/api/v1';

  static String validateApiBaseUrl(String env, String url) {
    if (env == 'production') {
      final uri = Uri.tryParse(url);
      if (uri == null ||
          uri.scheme != 'https' ||
          uri.host.isEmpty ||
          uri.host == 'localhost' ||
          uri.host == '127.0.0.1' ||
          uri.host == '10.0.2.2') {
        throw StateError(
          'Production requires a public HTTPS API URL. Pass '
          '--dart-define=API_BASE_URL=https://your-api-domain at build time.',
        );
      }
    }
    return url;
  }
  
  static const int apiTimeoutSeconds = int.fromEnvironment(
    'API_TIMEOUT_SECONDS',
    defaultValue: 30,
  );
  
  static const String environment = String.fromEnvironment(
    'ENVIRONMENT',
    defaultValue: kReleaseMode ? 'production' : 'development',
  );
  
  static const String sentryDsn = String.fromEnvironment(
    'SENTRY_DSN',
    defaultValue: '',
  );

  static const String appVersion = String.fromEnvironment(
    'APP_VERSION',
    defaultValue: '1.0.0',
  );

  static const String appCommit = String.fromEnvironment(
    'APP_COMMIT',
    defaultValue: 'dev',
  );
}
