import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_models.dart';

/// StorageService — persists auth tokens in secure storage and preferences in shared_preferences.
class StorageService {
  StorageService._();
  static final StorageService instance = StorageService._();

  static const _keyAccess = 'access_token';
  static const _keyRefresh = 'refresh_token';
  static const _keyOnboarding = 'onboarding_seen';
  static const _keyCachedUser = 'cached_user';
  static const String _keyLang = 'preferred_language';
  static const String _keyTheme = 'theme_mode';
  static const String _keyNotif = 'notifications_enabled';
  static const _keyProfessionalMode = 'professional_mode';
  static const _keyMedicalUnits = 'medical_units';
  static const _keyDismissedAnnouncements = 'dismissed_announcements';

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage(
    aOptions: AndroidOptions(),
    iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  );

  // ── Tokens (flutter_secure_storage with migration) ─────────────────────────

  Future<void> _migrateTokensIfNeeded() async {
    final prefs = await SharedPreferences.getInstance();
    final oldAccess = prefs.getString(_keyAccess);
    final oldRefresh = prefs.getString(_keyRefresh);
    
    if (oldAccess != null || oldRefresh != null) {
      if (oldAccess != null) {
        await _secureStorage.write(key: _keyAccess, value: oldAccess);
      }
      if (oldRefresh != null) {
        await _secureStorage.write(key: _keyRefresh, value: oldRefresh);
      }
      await prefs.remove(_keyAccess);
      await prefs.remove(_keyRefresh);
    }
  }

  Future<void> saveTokens(String access, String refresh) async {
    if (kIsWeb) {
      throw UnsupportedError('Secure token persistence is not supported on Flutter Web in this release. Use HttpOnly cookies instead.');
    }
    await _secureStorage.write(key: _keyAccess, value: access);
    await _secureStorage.write(key: _keyRefresh, value: refresh);
  }

  Future<String?> getAccessToken() async {
    if (kIsWeb) return null;
    await _migrateTokensIfNeeded();
    return _secureStorage.read(key: _keyAccess);
  }
  
  Future<String?> getRefreshToken() async {
    if (kIsWeb) return null;
    await _migrateTokensIfNeeded();
    return _secureStorage.read(key: _keyRefresh);
  }

  Future<void> clearTokens() async {
    if (!kIsWeb) {
      await _secureStorage.delete(key: _keyAccess);
      await _secureStorage.delete(key: _keyRefresh);
    }
    // Also clear from prefs just in case
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyAccess);
    await prefs.remove(_keyRefresh);
  }

  // ─────────────────────────── App Preferences ────────────────────────
  
  Future<void> setMedicalUnits(String units) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyMedicalUnits, units);
  }

  Future<String> getMedicalUnits() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyMedicalUnits) ?? 'metric';
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

  // ── Reminder Sound (shared_preferences) ──────────────────────────────────
  
  static const String _keyReminderSound = 'reminder_sound';

  Future<void> setReminderSound(String soundName) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyReminderSound, soundName);
  }

  Future<String> getReminderSound() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyReminderSound) ?? 'default';
  }

  // ── Announcements (shared_preferences) ──────────────────────────────────
  
  Future<void> dismissAnnouncement(String id) async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_keyDismissedAnnouncements) ?? [];
    if (!list.contains(id)) {
      list.add(id);
      await prefs.setStringList(_keyDismissedAnnouncements, list);
    }
  }

  Future<bool> isAnnouncementDismissed(String id) async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_keyDismissedAnnouncements) ?? [];
    return list.contains(id);
  }

  // ── Role Profile Isolation Storage ──────────────────────────────────────

  Future<void> saveDoctorProfile(String userId, DoctorProfileModel profile) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('doctor_profile_$userId', jsonEncode(profile.toMap()));
  }

  Future<DoctorProfileModel?> getDoctorProfile(String userId) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('doctor_profile_$userId');
    if (raw == null) return null;
    try {
      return DoctorProfileModel.fromMap(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> saveCaregiverProfile(String userId, CaregiverProfileModel profile) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('caregiver_profile_$userId', jsonEncode(profile.toMap()));
  }

  Future<CaregiverProfileModel?> getCaregiverProfile(String userId) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('caregiver_profile_$userId');
    if (raw == null) return null;
    try {
      return CaregiverProfileModel.fromMap(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> clearUserData(String? userId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyCachedUser);
    if (userId != null) {
      await prefs.remove('doctor_profile_$userId');
      await prefs.remove('caregiver_profile_$userId');
    }
  }
}
