import 'package:flutter/foundation.dart';

class AppConfig {
  static const bool isLocalDevMode = bool.fromEnvironment('LOCAL_DEV_MODE', defaultValue: kDebugMode);

  /// API_BASE_URL is always the backend origin (without /api/v1).
  static const String _rawApiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: isLocalDevMode ? 'http://127.0.0.1:8000' : '', 
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
    return validateApiBaseUrl(environment, url);
  }

  static String get apiRoot => '$apiBaseUrl/api/v1';

  static String validateApiBaseUrl(String env, String url) {
    if (env == 'production') {
      if (url.isEmpty) {
        throw StateError('Production deployment requires a real backend URL. Pass --dart-define=API_BASE_URL=https://... at build time.');
      }
      if (url.startsWith('http://')) {
        throw StateError('Production environment MUST use HTTPS for apiBaseUrl.');
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
    defaultValue: 'development',
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
