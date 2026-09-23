class AppConfig {
  static const String _rawApiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );
  
  static String get apiBaseUrl => validateApiBaseUrl(environment, _rawApiBaseUrl);

  static String validateApiBaseUrl(String env, String url) {
    if (env == 'production' && url.startsWith('http://')) {
      throw StateError('Production environment MUST use HTTPS for apiBaseUrl.');
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
}
