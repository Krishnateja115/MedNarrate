import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'dart:math';

class KeystoreService {
  KeystoreService._();
  static final KeystoreService instance = KeystoreService._();
  
  Future<List<int>> getEncryptionKey() async {
    final prefs = await SharedPreferences.getInstance();
    final keyString = prefs.getString('hive_encryption_key');
    if (keyString != null) {
      try {
        final decoded = base64Url.decode(keyString);
        if (decoded.length == 32) {
          return decoded;
        }
      } catch (_) {}
    }
    
    final secureRandom = Random.secure();
    final newKey = List<int>.generate(32, (i) => secureRandom.nextInt(256));
    await prefs.setString('hive_encryption_key', base64Url.encode(newKey));
    return newKey;
  }

  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('jwt_token', token);
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('jwt_token');
  }

  Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('jwt_token');
  }
}
