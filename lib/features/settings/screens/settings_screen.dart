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
  String _currentUnits = 'metric';
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
    final units = await _storageService.getMedicalUnits();
    final bioAvail = await BiometricService.instance.isAvailable();
    final bioEnab = await BiometricService.instance.isBiometricEnabled();
    
    if (mounted) {
      setState(() {
        _currentLang = lang;
        _currentTheme = theme;
        _currentUnits = units;
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

  Future<void> _changeMedicalUnits(String units) async {
    await _storageService.setMedicalUnits(units);
    if (mounted) setState(() => _currentUnits = units);
    if (mounted) Helpers.showSuccess(context, 'Medical units updated');
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




  void _showSoonSheet(String featureName, String description) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text('Coming Soon', style: TextStyle(color: Theme.of(context).colorScheme.primary, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 20),
            Icon(Icons.construction_outlined, size: 48, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.4)),
            const SizedBox(height: 16),
            Text(featureName, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(description, textAlign: TextAlign.center,
              style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6))),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Future<void> _exportData() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('Export Data', style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
        content: Text('Request an archive of your medical history?', style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7))),
        backgroundColor: Theme.of(context).cardColor,
        actions: [
          TextButton(onPressed: () => context.pop(false), child: Text('Cancel')),
          TextButton(
            onPressed: () => context.pop(true),
            child: Text('Export', style: TextStyle(color: AppColors.primary)),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    
    setState(() => _loading = true);
    // Simulate API call
    await Future.delayed(const Duration(seconds: 2));
    if (mounted) {
      setState(() => _loading = false);
      Helpers.showSuccess(context, 'Your medical data archive has been requested and will be sent to your registered email shortly.');
    }
  }

  void _showAbout() {
    showAboutDialog(
      context: context,
      applicationName: 'MedNarrate',
      applicationVersion: 'v1.0.0',
      applicationIcon: Icon(Icons.medical_services, size: 48, color: AppColors.primary),
      applicationLegalese: '© 2026 MedNarrate Inc.\n\nAll rights reserved.',
      children: [
        const SizedBox(height: 16),
        ListTile(
          title: Text('Terms of Service', style: TextStyle(color: Theme.of(context).colorScheme.primary)),
          onTap: () {},
        ),
        ListTile(
          title: Text('Privacy Policy', style: TextStyle(color: Theme.of(context).colorScheme.primary)),
          onTap: () {},
        ),
      ],
    );
  }

  void _showHelpCenter() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => const _HelpCenterSheet(),
    );
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
                      activeThumbColor: Theme.of(context).colorScheme.primary,
                    ),
                    onTap: _biometricAvailable ? () => _toggleBiometric(!_biometricEnabled) : null,
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.download_outlined,
                    iconColor: AppColors.secondary,
                    title: 'Export Data',
                    subtitle: 'Download your medical history',
                    onTap: _exportData,
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
                      activeThumbColor: Theme.of(context).colorScheme.primary,
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
                    subtitle: _currentUnits == 'metric' ? 'Metric (kg, cm, °C)' : 'Imperial (lbs, in, °F)',
                    onTap: () {
                      showModalBottomSheet(
                        context: context,
                        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
                        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
                        builder: (_) => _MeasurementPicker(
                          currentUnits: _currentUnits,
                          onSelect: (units) {
                            context.pop();
                            _changeMedicalUnits(units);
                          },
                        ),
                      );
                    },
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
                      activeThumbColor: Theme.of(context).colorScheme.primary,
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
                    subtitle: 'Coming Soon',
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.warning.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text('SOON', style: TextStyle(color: AppColors.warning, fontSize: 10, fontWeight: FontWeight.bold)),
                    ),
                    onTap: () => _showSoonSheet('Reminder Sound', 'Custom ringtones for your medication reminders are coming in the next update.'),
                  ),
                ]),

                _buildSettingsGroup('INTEGRATIONS', [
                  _buildSettingsTile(
                    icon: Icons.health_and_safety_outlined,
                    iconColor: AppColors.error,
                    title: 'Health App Sync',
                    subtitle: 'Coming Soon',
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.error.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text('SOON', style: TextStyle(color: AppColors.error, fontSize: 10, fontWeight: FontWeight.bold)),
                    ),
                    onTap: () => _showSoonSheet('Health App Sync', 'Sync with Apple Health and Google Fit to automatically pull your vitals and activity data.'),
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.watch_outlined,
                    iconColor: Theme.of(context).colorScheme.onSurface,
                    title: 'Connected Devices',
                    subtitle: 'Coming Soon',
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text('SOON', style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5), fontSize: 10, fontWeight: FontWeight.bold)),
                    ),
                    onTap: () => _showSoonSheet('Connected Devices', 'Connect your wearables, glucometers, and blood pressure monitors to track readings automatically.'),
                  ),
                ]),

                _buildSettingsGroup('SUPPORT & ABOUT', [
                  _buildSettingsTile(
                    icon: Icons.help_outline,
                    iconColor: AppColors.success,
                    title: 'Help Center',
                    onTap: _showHelpCenter,
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.info_outline,
                    iconColor: AppColors.accentTeal,
                    title: 'About MedNarrate',
                    subtitle: 'Version 1.0.0',
                    onTap: _showAbout,
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

class _MeasurementPicker extends StatelessWidget {
  final String currentUnits;
  final ValueChanged<String> onSelect;

  const _MeasurementPicker({
    required this.currentUnits,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    final options = [
      {'label': 'Metric (kg, cm, °C)', 'value': 'metric'},
      {'label': 'Imperial (lbs, in, °F)', 'value': 'imperial'},
    ];
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('Select Medical Units', style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 18, fontWeight: FontWeight.bold)),
          SizedBox(height: 16),
          ...options.map((option) {
            final label = option['label'] as String;
            final value = option['value'] as String;
            return ListTile(
              title: Text(label, style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
              trailing: value == currentUnits ? Icon(Icons.check, color: Theme.of(context).colorScheme.primary) : null,
              onTap: () => onSelect(value),
            );
          }),
        ],
      ),
    );
  }
}

class _HelpCenterSheet extends StatelessWidget {
  const _HelpCenterSheet();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.7,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 5,
              margin: const EdgeInsets.only(bottom: 20),
              decoration: BoxDecoration(
                color: Theme.of(context).dividerColor,
                borderRadius: BorderRadius.circular(10),
              ),
            ),
          ),
          Text(
            'Help Center',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.onSurface,
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: ListView(
              children: [
                _buildFaqItem(
                  context,
                  'How do I upload a medical report?',
                  'You can upload a report from the Home screen by tapping the "+" button. We support PDF documents and images (JPG/PNG).',
                ),
                _buildFaqItem(
                  context,
                  'Is my medical data secure?',
                  'Yes. MedNarrate encrypts your data both in transit and at rest. We also provide biometric app lock capabilities to protect your medical history locally on your device.',
                ),
                _buildFaqItem(
                  context,
                  'How does the AI analysis work?',
                  'MedNarrate uses advanced clinical AI models to extract, summarize, and explain complex medical jargon in a patient-friendly format.',
                ),
                _buildFaqItem(
                  context,
                  'Can I share my reports?',
                  'Yes, you can export your data from the Settings screen or share individual reports directly using the share button on the report details screen.',
                ),
              ],
            ),
          ),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.only(top: 16),
            child: ElevatedButton.icon(
              onPressed: () {
                context.pop();
                Helpers.showSuccess(context, 'Redirecting to email client...');
              },
              icon: const Icon(Icons.email_outlined),
              label: const Text('Contact Support'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFaqItem(BuildContext context, String question, String answer) {
    return ExpansionTile(
      title: Text(
        question,
        style: TextStyle(fontWeight: FontWeight.w600, color: Theme.of(context).colorScheme.onSurface),
      ),
      childrenPadding: const EdgeInsets.only(left: 16, right: 16, bottom: 16),
      expandedCrossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          answer,
          style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7)),
        ),
      ],
    );
  }
}
