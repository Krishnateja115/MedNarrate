import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import 'dart:math';

class KeystoreService {
  KeystoreService._();
  static final KeystoreService instance = KeystoreService._();
  
  final _storage = const FlutterSecureStorage();
  
  Future<List<int>> getEncryptionKey() async {
    final keyString = await _storage.read(key: 'hive_encryption_key');
    if (keyString != null) {
      return base64Url.decode(keyString);
    } else {
      final secureRandom = Random.secure();
      final newKey = List<int>.generate(32, (i) => secureRandom.nextInt(256));
      await _storage.write(key: 'hive_encryption_key', value: base64Url.encode(newKey));
      return newKey;
    }
  }

  Future<void> saveToken(String token) async {
    await _storage.write(key: 'jwt_token', value: token);
  }

  Future<String?> getToken() async {
    return await _storage.read(key: 'jwt_token');
  }

  Future<void> clearToken() async {
    await _storage.delete(key: 'jwt_token');
  }
}
