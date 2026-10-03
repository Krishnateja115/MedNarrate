import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// In-memory stand-in for the flutter_secure_storage platform channel, so
/// tests that touch KeystoreService / ReminderService run without a device.
Map<String, String> installSecureStorageMock() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final store = <String, String>{};
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(
    const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
    (MethodCall call) async {
      final args = (call.arguments as Map?)?.cast<String, dynamic>() ?? {};
      final key = args['key'] as String?;
      switch (call.method) {
        case 'read':
          return store[key];
        case 'write':
          store[key!] = args['value'] as String;
          return null;
        case 'delete':
          store.remove(key);
          return null;
        case 'deleteAll':
          store.clear();
          return null;
        case 'readAll':
          return Map<String, String>.from(store);
        case 'containsKey':
          return store.containsKey(key);
      }
      return null;
    },
  );
  return store;
}
