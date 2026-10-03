import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:mednarrate/core/services/storage_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  test('tokens never written to SharedPreferences on save', () async {
    await StorageService.instance.saveTokens('access123', 'refresh456');

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('access_token'), isNull);
    expect(prefs.getString('refresh_token'), isNull);

    final access = await StorageService.instance.getAccessToken();
    final refresh = await StorageService.instance.getRefreshToken();
    expect(access, 'access123');
    expect(refresh, 'refresh456');
  });

  test('old token migration deletes plaintext values', () async {
    // Set old values
    SharedPreferences.setMockInitialValues({
      'access_token': 'legacy_access',
      'refresh_token': 'legacy_refresh',
    });

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('access_token'), 'legacy_access');

    // Trigger migration by reading
    final access = await StorageService.instance.getAccessToken();
    expect(access, 'legacy_access');
    
    // Verify deleted from SharedPreferences
    expect(prefs.getString('access_token'), isNull);
    expect(prefs.getString('refresh_token'), isNull);

    // Verify stored securely
    final refresh = await StorageService.instance.getRefreshToken();
    expect(refresh, 'legacy_refresh');
  });

  test('logout clears secure tokens', () async {
    await StorageService.instance.saveTokens('acc', 'ref');
    expect(await StorageService.instance.getAccessToken(), 'acc');

    await StorageService.instance.clearTokens();
    expect(await StorageService.instance.getAccessToken(), isNull);
    expect(await StorageService.instance.getRefreshToken(), isNull);
  });
}
