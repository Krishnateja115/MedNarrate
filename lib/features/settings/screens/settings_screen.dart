import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:app_settings/app_settings.dart';

import '../../../core/services/api_service.dart';
import '../../../core/services/storage_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/biometric_service.dart';
import '../../../core/utils/helpers.dart';
import 'package:go_router/go_router.dart';
import 'package:audioplayers/audioplayers.dart';

import '../../../core/routing/routes.dart';
import '../../../core/constants/app_colors.dart';
import '../../../main.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

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
  bool _loading = true;
  String _currentSound = 'default';
  
  final AudioPlayer _audioPlayer = AudioPlayer();

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
  
  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }

  BiometricAvailability _biometricStatus = BiometricAvailability.unsupported;

  Future<void> _loadSettings() async {
    final lang = await _storageService.getPreferredLanguage();
    final theme = await _storageService.getThemeMode();
    final notifs = await _storageService.getNotificationsEnabled();
    final profMode = await _storageService.getProfessionalMode();
    final units = await _storageService.getMedicalUnits();
    final bioStatus = await BiometricService.instance.checkAvailability();
    final bioEnab = await BiometricService.instance.isBiometricEnabled();
    final sound = await _storageService.getReminderSound();
    
    if (mounted) {
      setState(() {
        _currentLang = lang;
        _currentTheme = theme;
        _notificationsEnabled = notifs;
        _professionalMode = profMode;
        _currentUnits = units;
        _biometricStatus = bioStatus;
        _biometricEnabled = bioEnab;
        _currentSound = sound;
        _loading = false;
      });
    }
  }

  String get _biometricSubtitle {
    if (kIsWeb) {
      return 'Biometric App Lock is available on the mobile app (Android / iOS)';
    }
    if (_biometricEnabled) {
      return 'Protected with device biometric authentication';
    }
    switch (_biometricStatus) {
      case BiometricAvailability.available:
        return 'Use fingerprint or Face ID to protect the app';
      case BiometricAvailability.notConfigured:
        return 'Set up fingerprint or Face ID in device settings first';
      case BiometricAvailability.noPlatformAuthenticator:
        return 'Biometric authentication is not available on this device';
      case BiometricAvailability.webUnsupported:
      case BiometricAvailability.unsupported:
        return 'Biometric App Lock is available on the mobile app (Android / iOS)';
    }
  }

  Future<void> _toggleBiometric(bool enabled) async {
    if (kIsWeb) {
      Helpers.showError(context, 'Biometric App Lock requires a physical Android or iOS mobile device. It is not available in the web browser environment.');
      return;
    }
    if (!enabled) {
      final confirm = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text(AppLocalizations.of(context)!.disableAppLock, style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
          content: Text(AppLocalizations.of(context)!.appLockReportsAccessible, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7))),
          backgroundColor: Theme.of(context).cardColor,
          actions: [
            TextButton(onPressed: () => context.pop(false), child: Text(AppLocalizations.of(context)!.cancel)),
            TextButton(
              onPressed: () => context.pop(true),
              child: Text(AppLocalizations.of(context)!.disable, style: TextStyle(color: Colors.red)),
            ),
          ],
        ),
      );
      if (confirm != true) return;
    } else {
      if (_biometricStatus == BiometricAvailability.noPlatformAuthenticator) {
        Helpers.showError(context, 'Biometric authentication is not available on this device.');
        return;
      }
      if (_biometricStatus == BiometricAvailability.notConfigured) {
        Helpers.showError(context, 'Please set up fingerprint or Face ID in your device settings first.');
        return;
      }
    }

    final result = await BiometricService.instance.setBiometricEnabled(enabled);
    if (!mounted) return;

    if (result == BiometricResult.success) {
      setState(() => _biometricEnabled = enabled);
      if (enabled) {
        Helpers.showSuccess(context, 'Biometric App Lock enabled successfully.');
      } else {
        Helpers.showSuccess(context, 'Biometric App Lock disabled.');
      }
    } else if (result == BiometricResult.cancelled) {
      Helpers.showError(context, 'Authentication cancelled.');
    } else if (result == BiometricResult.notConfigured) {
      Helpers.showError(context, 'Please set up fingerprint or Face ID in your device settings first.');
    } else {
      Helpers.showError(context, 'Biometric authentication failed. Please try again.');
    }
  }

  Future<void> _changeBiometric() async {
    if (kIsWeb) {
      Helpers.showError(context, 'Biometric management requires a physical Android or iOS mobile device.');
      return;
    }
    if (!_biometricEnabled) return;

    // STEP 1: Require authentication of current biometric
    final authRes = await BiometricService.instance.verifyCurrentBiometric();
    if (!mounted) return;

    if (authRes == BiometricResult.cancelled) {
      Helpers.showError(context, 'Biometric change cancelled.');
      return;
    } else if (authRes != BiometricResult.success) {
      Helpers.showError(context, 'Authentication failed. Your biometric settings have not been changed.');
      return;
    }

    // STEP 2: Current authentication succeeded -> Guide user to device settings to add/update fingerprint/Face ID
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: Theme.of(ctx).cardColor,
        title: Row(
          children: [
            Icon(Icons.fingerprint, color: AppColors.accentTeal),
            const SizedBox(width: 10),
            Text(
              'Change Device Biometrics',
              style: TextStyle(color: Theme.of(ctx).colorScheme.onSurface, fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Current biometric verified successfully!\n\nTo add or update your fingerprint or Face ID, manage your biometrics in your mobile device settings:',
              style: TextStyle(color: Theme.of(ctx).colorScheme.onSurface.withValues(alpha: 0.8), fontSize: 15),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () async {
                  ctx.pop();
                  try {
                    await AppSettings.openAppSettings(type: AppSettingsType.security);
                  } catch (_) {}
                },
                icon: const Icon(Icons.settings, size: 18),
                label: const Text('Open Device Security Settings', style: TextStyle(fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.accentTeal,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => ctx.pop(),
            child: const Text('Done'),
          ),
        ],
      ),
    );
  }

  Future<void> _changeLanguage(String lang) async {
    setState(() => _loading = true);
    try {
      await _apiService.updateMe(preferredLanguage: lang);
      await _storageService.setPreferredLanguage(lang);
      localeModeNotifier.value = Locale(lang);
      if (mounted) setState(() => _currentLang = lang);
      if (mounted) Helpers.showSuccess(context, AppLocalizations.of(context)!.languageUpdated);
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
    if (mounted) Helpers.showSuccess(context, AppLocalizations.of(context)!.medicalUnitsUpdated);
  }

  Future<void> _toggleNotifications(bool enabled) async {
    await _storageService.setNotificationsEnabled(enabled);
    if (!mounted) return;
    setState(() => _notificationsEnabled = enabled);
    
    if (enabled) {
      Helpers.showSuccess(context, AppLocalizations.of(context)!.notificationsEnabled);
    } else {
      Helpers.showSuccess(context, AppLocalizations.of(context)!.notificationsDisabled);
    }
  }

  Future<void> _changeReminderSound(String sound) async {
    await _storageService.setReminderSound(sound);
    if (mounted) setState(() => _currentSound = sound);
  }

  void _playSound(String sound) {
    if (sound == 'default') return; // Cannot play system default easily via audioplayers without knowing URI
    _audioPlayer.play(AssetSource('sounds/$sound.wav'));
  }

  void _showSoundPicker() {
    final sounds = {
      'default': 'System Default',
      'chime': 'Crystal Chime',
      'warm_chord': 'Warm Chord',
      'nature_drop': 'Nature Drop',
    };

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setSheetState) {
            return Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey.withValues(alpha: 0.3), borderRadius: BorderRadius.circular(2))),
                  const SizedBox(height: 24),
                  Text(AppLocalizations.of(context)!.reminderSound, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 24),
                  ...sounds.entries.map((e) {
                    final isSelected = _currentSound == e.key;
                    return ListTile(
                      title: Text(e.value),
                      trailing: isSelected ? const Icon(Icons.check, color: AppColors.primary) : null,
                      onTap: () {
                        _playSound(e.key);
                        _changeReminderSound(e.key);
                        setSheetState(() {});
                      },
                    );
                  }),
                  const SizedBox(height: 24),
                ],
              ),
            );
          }
        );
      },
    );
  }

  Future<void> _toggleProfessionalMode(bool enabled) async {
    await _storageService.setProfessionalMode(enabled);
    if (mounted) setState(() => _professionalMode = enabled);
    if (mounted) Helpers.showSuccess(context, enabled ? 'Professional Mode enabled' : 'Professional Mode disabled');
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
              child: Text(AppLocalizations.of(context)!.comingSoon, style: TextStyle(color: Theme.of(context).colorScheme.primary, fontWeight: FontWeight.bold)),
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
        title: Text(AppLocalizations.of(context)!.exportData, style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
        content: Text(AppLocalizations.of(context)!.requestArchive, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7))),
        backgroundColor: Theme.of(context).cardColor,
        actions: [
          TextButton(onPressed: () => context.pop(false), child: Text(AppLocalizations.of(context)!.cancel)),
          TextButton(
            onPressed: () => context.pop(true),
            child: Text(AppLocalizations.of(context)!.export, style: TextStyle(color: AppColors.primary)),
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
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context);

    showDialog(
      context: context,
      builder: (dialogContext) {
        return Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
          backgroundColor: theme.cardColor,
          insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 28),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // App Icon Badge
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.12),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.medical_services_rounded,
                      size: 38,
                      color: AppColors.primary,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // App Name & Version
                  Text(
                    'MedNarrate',
                    style: TextStyle(
                      color: theme.colorScheme.onSurface,
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.10),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Text(
                      'v1.0.0',
                      style: TextStyle(
                        color: AppColors.primary,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // Copyright & Legal Attribution
                  Text(
                    '© 2026 MedNarrate\nAll rights reserved.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                      fontSize: 13,
                      height: 1.4,
                    ),
                  ),

                  const SizedBox(height: 20),
                  Divider(
                    height: 1,
                    thickness: 1,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.08),
                  ),
                  const SizedBox(height: 14),

                  // Clickable Legal Links
                  Material(
                    color: Colors.transparent,
                    child: InkWell(
                      onTap: () {
                        Navigator.of(dialogContext).pop();
                        context.push(Routes.termsOfService);
                      },
                      borderRadius: BorderRadius.circular(12),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                const Icon(
                                  Icons.gavel_rounded,
                                  size: 18,
                                  color: AppColors.primary,
                                ),
                                const SizedBox(width: 12),
                                Text(
                                  l10n?.termsOfService ?? 'Terms of Service',
                                  style: TextStyle(
                                    color: theme.colorScheme.onSurface,
                                    fontSize: 14.5,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ],
                            ),
                            Icon(
                              Icons.arrow_forward_ios_rounded,
                              size: 14,
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  Material(
                    color: Colors.transparent,
                    child: InkWell(
                      onTap: () {
                        Navigator.of(dialogContext).pop();
                        context.push(Routes.privacyPolicy);
                      },
                      borderRadius: BorderRadius.circular(12),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                const Icon(
                                  Icons.privacy_tip_outlined,
                                  size: 18,
                                  color: AppColors.primary,
                                ),
                                const SizedBox(width: 12),
                                Text(
                                  l10n?.privacyPolicy ?? 'Privacy Policy',
                                  style: TextStyle(
                                    color: theme.colorScheme.onSurface,
                                    fontSize: 14.5,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ],
                            ),
                            Icon(
                              Icons.arrow_forward_ios_rounded,
                              size: 14,
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 14),
                  Divider(
                    height: 1,
                    thickness: 1,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.08),
                  ),
                  const SizedBox(height: 18),

                  // Bottom Action Buttons
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      TextButton.icon(
                        onPressed: () {
                          Navigator.of(dialogContext).pop();
                          context.push(Routes.customLicenses);
                        },
                        icon: const Icon(Icons.code_rounded, size: 18),
                        label: const Text('View Licenses'),
                        style: TextButton.styleFrom(
                          foregroundColor: AppColors.primary,
                          textStyle: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ),
                      ElevatedButton(
                        onPressed: () => Navigator.of(dialogContext).pop(),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          foregroundColor: Colors.white,
                          elevation: 0,
                          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: const Text('Close'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        );
      },
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
        title: Text(AppLocalizations.of(context)!.settings, style: TextStyle(fontWeight: FontWeight.bold)),
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
                    title: AppLocalizations.of(context)!.personalInformation,
                    subtitle: 'Update your basic profile details',
                    onTap: () => context.push(Routes.profile),
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.shield_outlined,
                    iconColor: AppColors.accentTeal,
                    title: 'Biometric App Lock',
                    subtitle: _biometricSubtitle,
                    trailing: Switch(
                      value: _biometricEnabled,
                      onChanged: !kIsWeb && (_biometricStatus == BiometricAvailability.available || _biometricEnabled)
                          ? _toggleBiometric
                          : null,
                      activeThumbColor: Theme.of(context).colorScheme.primary,
                    ),
                    onTap: () {
                      if (kIsWeb) {
                        Helpers.showError(context, 'Biometric App Lock is available when running on a mobile device (Android / iOS).');
                      } else if (_biometricStatus == BiometricAvailability.available || _biometricEnabled) {
                        _toggleBiometric(!_biometricEnabled);
                      }
                    },
                  ),
                  if (_biometricEnabled && !kIsWeb) ...[
                    Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                    _buildSettingsTile(
                      icon: Icons.fingerprint,
                      iconColor: AppColors.primary,
                      title: 'Change Biometric',
                      subtitle: 'Re-verify & manage device biometric settings',
                      onTap: _changeBiometric,
                    ),
                  ],
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.download_outlined,
                    iconColor: AppColors.secondary,
                    title: AppLocalizations.of(context)!.exportData,
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
                    title: AppLocalizations.of(context)!.professionalMode,
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
                    title: AppLocalizations.of(context)!.language,
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
                    title: AppLocalizations.of(context)!.medicalUnits,
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
                    subtitle: AppLocalizations.of(context)!.notificationsSubtitle,
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
                    title: AppLocalizations.of(context)!.medicationSchedules,
                    subtitle: AppLocalizations.of(context)!.managePillReminders,
                    onTap: () => context.push(Routes.medications),
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.alarm,
                    iconColor: AppColors.warning,
                    title: AppLocalizations.of(context)!.reminderSound,
                    subtitle: _currentSound == 'default' ? 'System Default' : _currentSound.replaceAll('_', ' ').split(' ').map((w) => w[0].toUpperCase() + w.substring(1)).join(' '),
                    onTap: _showSoundPicker,
                  ),
                ]),

                _buildSettingsGroup('INTEGRATIONS', [
                  _buildSettingsTile(
                    icon: Icons.health_and_safety_outlined,
                    iconColor: AppColors.error,
                    title: AppLocalizations.of(context)!.healthAppSync,
                    subtitle: AppLocalizations.of(context)!.comingSoon,
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
                    title: AppLocalizations.of(context)!.connectedDevices,
                    subtitle: AppLocalizations.of(context)!.comingSoon,
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
                    title: AppLocalizations.of(context)!.helpCenter,
                    onTap: _showHelpCenter,
                  ),
                  Divider(height: 1, indent: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.1)),
                  _buildSettingsTile(
                    icon: Icons.info_outline,
                    iconColor: AppColors.accentTeal,
                    title: AppLocalizations.of(context)!.aboutMedNarrate,
                    subtitle: AppLocalizations.of(context)!.version,
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
          Text(AppLocalizations.of(context)!.selectLanguage, style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 18, fontWeight: FontWeight.bold)),
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
          Text(AppLocalizations.of(context)!.selectThemeMode, style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 18, fontWeight: FontWeight.bold)),
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
          Text(AppLocalizations.of(context)!.selectMedicalUnits, style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 18, fontWeight: FontWeight.bold)),
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
          Text(AppLocalizations.of(context)!.helpCenter,
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
              label: Text(AppLocalizations.of(context)!.contactSupport),
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
