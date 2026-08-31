class AppConfig {
  // For real Android device: flutter run --dart-define=API_BASE_URL=http://192.168.x.x:8000/api/v1
  // For emulator: uses 10.0.2.2:8000 automatically
  // For production: flutter run --dart-define=API_BASE_URL=https://api.mednarrate.com/api/v1
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );
  
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
