import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_models.dart';

/// StorageService — persists auth tokens in flutter_secure_storage;
/// everything else (onboarding, language, cached profile) in shared_preferences.
class StorageService {
  StorageService._();
  static final StorageService instance = StorageService._();

  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static const _keyAccess = 'access_token';
  static const _keyRefresh = 'refresh_token';
  static const _keyOnboarding = 'onboarding_seen';
  static const _keyCachedUser = 'cached_user';
  static const String _keyLang = 'preferred_language';
  static const String _keyTheme = 'theme_mode';
  static const String _keyNotif = 'notifications_enabled';
  static const String _keyProfessionalMode = 'professional_mode';

  // ── Tokens (flutter_secure_storage) ──────────────────────────────────

  Future<void> saveTokens(String access, String refresh) async {
    await _storage.write(key: _keyAccess, value: access);
    await _storage.write(key: _keyRefresh, value: refresh);
  }

  Future<String?> getAccessToken() => _storage.read(key: _keyAccess);
  Future<String?> getRefreshToken() => _storage.read(key: _keyRefresh);

  Future<void> clearTokens() async {
    await _storage.delete(key: _keyAccess);
    await _storage.delete(key: _keyRefresh);
  }

  // ── Onboarding (shared_preferences) ──────────────────────────────────

  Future<void> setOnboardingSeen() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyOnboarding, true);
  }

  Future<bool> isOnboardingSeen() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_keyOnboarding) ?? false;
  }

  // ── Cached user profile (shared_preferences, JSON string) ────────────

  Future<void> cacheUserProfile(UserModel user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyCachedUser, jsonEncode(user.toMap()));
  }

  Future<UserModel?> getCachedProfile() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_keyCachedUser);
    if (raw == null) return null;
    try {
      return UserModel.fromMap(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  // ── Language (shared_preferences) ────────────────────────────────────

  Future<void> setPreferredLanguage(String lang) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyLang, lang);
  }

  Future<String> getPreferredLanguage() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyLang) ?? 'en';
  }

  // ── Professional Mode (shared_preferences) ────────────────────────────

  Future<void> setProfessionalMode(bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyProfessionalMode, enabled);
  }

  Future<bool> getProfessionalMode() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_keyProfessionalMode) ?? false;
  }

  // ── Theme Mode (shared_preferences) ──────────────────────────────────

  Future<void> setThemeMode(ThemeMode mode) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyTheme, mode.name);
  }

  Future<ThemeMode> getThemeMode() async {
    final prefs = await SharedPreferences.getInstance();
    final name = prefs.getString(_keyTheme) ?? ThemeMode.system.name;
    return ThemeMode.values.firstWhere((e) => e.name == name, orElse: () => ThemeMode.system);
  }

  // ── Notifications (shared_preferences) ──────────────────────────────────

  Future<void> setNotificationsEnabled(bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyNotif, enabled);
  }

  Future<bool> getNotificationsEnabled() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_keyNotif) ?? true;
  }

  // ── Biometric (shared_preferences) ──────────────────────────────────

  static const String _keyBiometric = 'biometric_enabled';

  Future<void> setBiometricEnabled(bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyBiometric, enabled);
  }

  Future<bool> getBiometricEnabled() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_keyBiometric) ?? false;
  }
}
