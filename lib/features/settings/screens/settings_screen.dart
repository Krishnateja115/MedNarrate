import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/storage_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/routing/routes.dart';
import 'package:go_router/go_router.dart';
import '../../../main.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final StorageService _storageService = StorageService.instance;
  final ApiService _apiService = ApiService.instance;

  String _currentLang = 'en';
  ThemeMode _currentTheme = ThemeMode.system;
  bool _notificationsEnabled = true;
  bool _loading = true;

  final Map<String, String> _languages = {
    'en': 'English',
    'hi': 'Hindi (हिन्दी)',
    'ta': 'Tamil (தமிழ்)',
    'te': 'Telugu (తెలుగు)',
    'kn': 'Kannada (ಕನ್ನಡ)',
    'ml': 'Malayalam (മലയാളം)',
    'mr': 'Marathi (मराठी)',
    'bn': 'Bengali (বাংলা)',
  };

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final lang = await _storageService.getPreferredLanguage();
    final theme = await _storageService.getThemeMode();
    final notifs = await _storageService.getNotificationsEnabled();
    if (mounted) {
      setState(() {
        _currentLang = lang;
        _currentTheme = theme;
        _notificationsEnabled = notifs;
        _loading = false;
      });
    }
  }

  Future<void> _changeLanguage(String lang) async {
    setState(() => _loading = true);
    try {
      await _apiService.updateMe(preferredLanguage: lang);
      await _storageService.setPreferredLanguage(lang);
      if (mounted) setState(() => _currentLang = lang);
      if (mounted) Helpers.showSuccess(context, 'Language updated successfully');
    } on ApiException catch (e) {
      if (mounted) Helpers.showError(context, e.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _changeTheme(ThemeMode mode) async {
    await _storageService.setThemeMode(mode);
    themeModeNotifier.value = mode;
    if (mounted) setState(() => _currentTheme = mode);
  }

  Future<void> _toggleNotifications(bool enabled) async {
    await _storageService.setNotificationsEnabled(enabled);
    if (mounted) setState(() => _notificationsEnabled = enabled);
    if (mounted) Helpers.showSuccess(context, enabled ? 'Notifications enabled' : 'Notifications disabled');
  }

  Future<void> _logout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Logout'),
        content: const Text('Are you sure you want to log out?'),
        actions: [
          TextButton(onPressed: () => context.pop(false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => context.pop(true),
            child: const Text('Logout', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    
    setState(() => _loading = true);
    try {
      await _apiService.logout();
    } catch (_) {
      // Ignore API errors on logout
    } finally {
      await _storageService.clearTokens();
      if (mounted) {
        context.go(Routes.login);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Settings'),
        backgroundColor: AppColors.background,
        elevation: 0,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Preferences', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  
                  // Language Selection
                  Container(
                    decoration: BoxDecoration(
                      color: AppColors.card,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: ListTile(
                      leading: const Icon(Icons.language, color: Colors.blue),
                      title: const Text('Preferred Language', style: TextStyle(color: Colors.white)),
                      subtitle: Text(_languages[_currentLang] ?? 'English', style: const TextStyle(color: Colors.white54)),
                      trailing: const Icon(Icons.arrow_forward_ios, color: Colors.white38, size: 16),
                      onTap: () {
                        showModalBottomSheet(
                          context: context,
                          backgroundColor: AppColors.background,
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
                          builder: (_) => _LanguagePicker(
                            languages: _languages,
                            currentLang: _currentLang,
                            onSelect: (lang) {
                              context.pop();
                              _changeLanguage(lang);
                            },
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 12),
                  
                  // Theme Selection
                  Container(
                    decoration: BoxDecoration(
                      color: AppColors.card,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: ListTile(
                      leading: const Icon(Icons.dark_mode_outlined, color: Colors.blue),
                      title: const Text('Theme Mode', style: TextStyle(color: Colors.white)),
                      subtitle: Text(
                        _currentTheme == ThemeMode.system ? 'System' : (_currentTheme == ThemeMode.light ? 'Light' : 'Dark'),
                        style: const TextStyle(color: Colors.white54),
                      ),
                      trailing: const Icon(Icons.arrow_forward_ios, color: Colors.white38, size: 16),
                      onTap: () {
                        showModalBottomSheet(
                          context: context,
                          backgroundColor: AppColors.background,
                          shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
                          builder: (_) => _ThemePicker(
                            currentTheme: _currentTheme,
                            onSelect: (mode) {
                              context.pop();
                              _changeTheme(mode);
                            },
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 12),
                  
                  // Notification Toggle
                  Container(
                    decoration: BoxDecoration(
                      color: AppColors.card,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: SwitchListTile(
                      secondary: const Icon(Icons.notifications_none, color: Colors.blue),
                      title: const Text('Local Notifications', style: TextStyle(color: Colors.white)),
                      subtitle: const Text('Enable medicine reminders & alerts', style: TextStyle(color: Colors.white54)),
                      value: _notificationsEnabled,
                      onChanged: _toggleNotifications,
                      activeThumbColor: Colors.blue,
                    ),
                  ),
                  
                  const SizedBox(height: 40),
                  
                  // Logout Button
                  SizedBox(
                    width: double.infinity,
                    height: 55,
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                      onPressed: _logout,
                      icon: const Icon(Icons.logout, color: Colors.white),
                      label: const Text('Logout', style: TextStyle(fontSize: 18, color: Colors.white)),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}

class _LanguagePicker extends StatelessWidget {
  final Map<String, String> languages;
  final String currentLang;
  final ValueChanged<String> onSelect;

  const _LanguagePicker({
    required this.languages,
    required this.currentLang,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('Select Language', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              itemCount: languages.length,
              itemBuilder: (context, index) {
                final key = languages.keys.elementAt(index);
                final value = languages.values.elementAt(index);
                return ListTile(
                  title: Text(value, style: const TextStyle(color: Colors.white)),
                  trailing: key == currentLang ? const Icon(Icons.check, color: Colors.blue) : null,
                  onTap: () => onSelect(key),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _ThemePicker extends StatelessWidget {
  final ThemeMode currentTheme;
  final ValueChanged<ThemeMode> onSelect;

  const _ThemePicker({
    required this.currentTheme,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    final options = [
      {'label': 'System', 'value': ThemeMode.system},
      {'label': 'Light', 'value': ThemeMode.light},
      {'label': 'Dark', 'value': ThemeMode.dark},
    ];
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('Select Theme Mode', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          ...options.map((option) {
            final label = option['label'] as String;
            final value = option['value'] as ThemeMode;
            return ListTile(
              title: Text(label, style: const TextStyle(color: Colors.white)),
              trailing: value == currentTheme ? const Icon(Icons.check, color: Colors.blue) : null,
              onTap: () => onSelect(value),
            );
          }),
        ],
      ),
    );
  }
}
