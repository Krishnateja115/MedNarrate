import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'dart:math';

import 'secure_storage_config.dart';

class KeystoreService {
  KeystoreService._();
  static final KeystoreService instance = KeystoreService._();

  final FlutterSecureStorage _secureStorage = appSecureStorage;

  Future<List<int>> getEncryptionKey() async {
    final prefs = await SharedPreferences.getInstance();

    // Check secure storage first
    String? keyString = await _secureStorage.read(key: 'hive_encryption_key');

    // Migration: If not in secure storage, check shared preferences
    if (keyString == null) {
      keyString = prefs.getString('hive_encryption_key');
      if (keyString != null) {
        // Validate and migrate
        try {
          final decoded = base64Url.decode(keyString);
          if (decoded.length == 32) {
            await _secureStorage.write(
                key: 'hive_encryption_key', value: keyString);
            await prefs.remove('hive_encryption_key');
            return decoded;
          }
        } catch (_) {}
      }
    } else {
      try {
        final decoded = base64Url.decode(keyString);
        if (decoded.length == 32) {
          return decoded;
        }
      } catch (_) {}
    }

    // Generate new key
    final secureRandom = Random.secure();
    final newKey = List<int>.generate(32, (i) => secureRandom.nextInt(256));
    await _secureStorage.write(
        key: 'hive_encryption_key', value: base64Url.encode(newKey));
    return newKey;
  }

  Future<void> saveToken(String token) async {
    // Also remove from SharedPreferences to prevent legacy exposure
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('jwt_token');
    await _secureStorage.write(key: 'jwt_token', value: token);
  }

  Future<String?> getToken() async {
    // Migration: Check SharedPreferences if secure storage is empty
    String? token = await _secureStorage.read(key: 'jwt_token');
    if (token == null) {
      final prefs = await SharedPreferences.getInstance();
      token = prefs.getString('jwt_token');
      if (token != null) {
        await saveToken(token); // saves to secure, removes from prefs
      }
    }
    return token;
  }

  Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('jwt_token');
    await _secureStorage.delete(key: 'jwt_token');
  }
}
