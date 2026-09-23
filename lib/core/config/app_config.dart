class AppConfig {
  static const bool isLocalDevMode = bool.fromEnvironment('LOCAL_DEV_MODE', defaultValue: false);

  static const String _rawApiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: isLocalDevMode ? 'http://127.0.0.1:8000' : 'https://api.mednarrate.com', // TODO: replace with real deployed backend URL
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

  static const String appVersion = String.fromEnvironment(
    'APP_VERSION',
    defaultValue: '1.0.0',
  );

  static const String appCommit = String.fromEnvironment(
    'APP_COMMIT',
    defaultValue: 'dev',
  );
}
