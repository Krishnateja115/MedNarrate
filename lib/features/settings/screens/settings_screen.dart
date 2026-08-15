import 'package:flutter/material.dart';

import '../../../core/services/api_service.dart';
import '../../../core/services/storage_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/biometric_service.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/routing/routes.dart';
import '../../../core/constants/app_colors.dart';
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
  bool _professionalMode = false;
  bool _biometricEnabled = false;
  bool _biometricAvailable = false;
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
    final profMode = await _storageService.getProfessionalMode();
    final bioAvail = await BiometricService.instance.isAvailable();
    final bioEnab = await BiometricService.instance.isBiometricEnabled();
    
    if (mounted) {
      setState(() {
        _currentLang = lang;
        _currentTheme = theme;
        _notificationsEnabled = notifs;
        _professionalMode = profMode;
        _biometricAvailable = bioAvail;
        _biometricEnabled = bioEnab;
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

  Future<void> _toggleProfessionalMode(bool enabled) async {
    await _storageService.setProfessionalMode(enabled);
    if (mounted) setState(() => _professionalMode = enabled);
    if (mounted) Helpers.showSuccess(context, enabled ? 'Professional Mode enabled' : 'Professional Mode disabled');
  }

  Future<void> _toggleBiometric(bool enabled) async {
    if (!_biometricAvailable) {
      Helpers.showError(context, 'Biometrics not available on this device.');
      return;
    }

    if (!enabled) {
      final confirm = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text('Disable App Lock?', style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
          content: Text('Your reports will be accessible without biometrics.', style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7))),
          backgroundColor: Theme.of(context).cardColor,
          actions: [
            TextButton(onPressed: () => context.pop(false), child: Text('Cancel')),
            TextButton(
              onPressed: () => context.pop(true),
              child: Text('Disable', style: TextStyle(color: Colors.red)),
            ),
          ],
        ),
      );
      if (confirm != true) return;
    }

    final success = await BiometricService.instance.setBiometricEnabled(enabled);
    if (success) {
      if (mounted) setState(() => _biometricEnabled = enabled);
    } else {
      if (mounted) Helpers.showError(context, 'Authentication failed. Biometric lock was not changed.');
    }
  }

  Future<void> _logout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('Logout', style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
        content: Text('Are you sure you want to log out?', style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7))),
        backgroundColor: Theme.of(context).cardColor,
        actions: [
          TextButton(onPressed: () => context.pop(false), child: Text('Cancel')),
          TextButton(
            onPressed: () => context.pop(true),
            child: Text('Logout', style: TextStyle(color: Colors.red)),
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

  void _showComingSoon() {
    Helpers.showSuccess(context, 'This feature is coming soon!');
  }

  Widget _buildSettingsGroup(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 8, bottom: 12, top: 24),
          child: Text(
            title,
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
              fontSize: 14,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.2,
            ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Theme.of(context).dividerColor.withValues(alpha: 0.05)),
          ),
          child: Column(
            children: children,
          ),
        ),
      ],
    );
  }

  Widget _buildSettingsTile({
    required IconData icon,
    required Color iconColor,
    required String title,
    String? subtitle,
    Widget? trailing,
    VoidCallback? onTap,
    bool isDestructive = false,
  }) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
      leading: Container(
        padding: EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: iconColor.withValues(alpha: 0.15),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: iconColor, size: 22),
      ),
      title: Text(
        title,
        style: TextStyle(
          color: isDestructive ? Colors.red : Theme.of(context).colorScheme.onSurface,
          fontWeight: FontWeight.w600,
          fontSize: 16,
        ),
      ),
      subtitle: subtitle != null
          ? Text(
              subtitle,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                fontSize: 13,
              ),
            )
          : null,
      trailing: trailing ??
          Icon(
            Icons.arrow_forward_ios,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.2),
            size: 16,
          ),
      onTap: onTap,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text('Settings', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              children: [
                _buildSettingsGroup('ACCOUNT & PROFILE', [
                  _buildSettingsTile(
                    icon: Icons.person_outline,
                    iconColor: Theme.of(context).colorScheme.primary,
                    title: 'Personal Information',
                    subtitle: 'Update your basic profile details',
                    onTap: () => context.push(Routes.profile),
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.shield_outlined,
                    iconColor: AppColors.accentTeal,
                    title: 'Biometric App Lock',
                    subtitle: _biometricAvailable ? 'Require Face ID / Fingerprint to open' : 'Not available on this device',
                    trailing: Switch(
                      value: _biometricEnabled,
                      onChanged: _biometricAvailable ? _toggleBiometric : null,
                      activeColor: Theme.of(context).colorScheme.primary,
                    ),
                    onTap: _biometricAvailable ? () => _toggleBiometric(!_biometricEnabled) : null,
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.download_outlined,
                    iconColor: AppColors.secondary,
                    title: 'Export Data',
                    subtitle: 'Download your medical history',
                    onTap: _showComingSoon,
                  ),
                ]),

                _buildSettingsGroup('APP PREFERENCES', [
                  _buildSettingsTile(
                    icon: Icons.dark_mode_outlined,
                    iconColor: AppColors.primary,
                    title: 'Theme',
                    subtitle: _currentTheme == ThemeMode.system
                        ? 'System Default'
                        : (_currentTheme == ThemeMode.light ? 'Light Mode' : 'Dark Mode'),
                    onTap: () {
                      showModalBottomSheet(
                        context: context,
                        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
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
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.medical_services_outlined,
                    iconColor: AppColors.primary,
                    title: 'Professional Mode',
                    subtitle: 'Show clinical summaries instead of patient-friendly ones',
                    trailing: Switch(
                      value: _professionalMode,
                      onChanged: _toggleProfessionalMode,
                      activeColor: Theme.of(context).colorScheme.primary,
                    ),
                    onTap: () => _toggleProfessionalMode(!_professionalMode),
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.language,
                    iconColor: AppColors.accentGold,
                    title: 'Language',
                    subtitle: _languages[_currentLang] ?? 'English',
                    onTap: () {
                      showModalBottomSheet(
                        context: context,
                        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
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
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.straighten,
                    iconColor: Theme.of(context).colorScheme.onSurface,
                    title: 'Medical Units',
                    subtitle: 'Metric (kg, cm, Celsius)',
                    onTap: _showComingSoon,
                  ),
                ]),

                _buildSettingsGroup('NOTIFICATIONS', [
                  _buildSettingsTile(
                    icon: Icons.notifications_active_outlined,
                    iconColor: AppColors.primary,
                    title: 'Push Notifications',
                    subtitle: 'Enable medicine reminders & alerts',
                    trailing: Switch(
                      value: _notificationsEnabled,
                      onChanged: _toggleNotifications,
                      activeColor: Theme.of(context).colorScheme.primary,
                    ),
                    onTap: () => _toggleNotifications(!_notificationsEnabled),
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.medication,
                    iconColor: AppColors.error,
                    title: 'Medication Schedules',
                    subtitle: 'Manage your automated pill reminders',
                    onTap: () => context.push(Routes.medications),
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.alarm,
                    iconColor: AppColors.warning,
                    title: 'Reminder Sound',
                    subtitle: 'Default chime',
                    onTap: _showComingSoon,
                  ),
                ]),

                _buildSettingsGroup('INTEGRATIONS', [
                  _buildSettingsTile(
                    icon: Icons.health_and_safety_outlined,
                    iconColor: AppColors.error,
                    title: 'Health App Sync',
                    subtitle: 'Connect to Apple Health / Google Fit',
                    onTap: _showComingSoon,
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.watch_outlined,
                    iconColor: Theme.of(context).colorScheme.onSurface,
                    title: 'Connected Devices',
                    subtitle: 'Manage wearables & monitors',
                    onTap: _showComingSoon,
                  ),
                ]),

                _buildSettingsGroup('SUPPORT & ABOUT', [
                  _buildSettingsTile(
                    icon: Icons.help_outline,
                    iconColor: AppColors.success,
                    title: 'Help Center',
                    onTap: _showComingSoon,
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.info_outline,
                    iconColor: AppColors.accentTeal,
                    title: 'About MedNarrate',
                    subtitle: 'Version 1.0.0',
                    onTap: _showComingSoon,
                  ),
                ]),

                const SizedBox(height: 32),
              ],
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
          Text('Select Language', style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 18, fontWeight: FontWeight.bold)),
          SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              itemCount: languages.length,
              itemBuilder: (context, index) {
                final key = languages.keys.elementAt(index);
                final value = languages.values.elementAt(index);
                return ListTile(
                  title: Text(value, style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
                  trailing: key == currentLang ? Icon(Icons.check, color: Theme.of(context).colorScheme.primary) : null,
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
      {'label': 'System Default', 'value': ThemeMode.system},
      {'label': 'Light Mode', 'value': ThemeMode.light},
      {'label': 'Dark Mode', 'value': ThemeMode.dark},
    ];
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('Select Theme Mode', style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 18, fontWeight: FontWeight.bold)),
          SizedBox(height: 16),
          ...options.map((option) {
            final label = option['label'] as String;
            final value = option['value'] as ThemeMode;
            return ListTile(
              title: Text(label, style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
              trailing: value == currentTheme ? Icon(Icons.check, color: Theme.of(context).colorScheme.primary) : null,
              onTap: () => onSelect(value),
            );
          }),
        ],
      ),
    );
  }
}
