import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_models.dart';
import '../../../core/routing/routes.dart';
import '../../../shared/widgets/profile_tile.dart';
import 'package:go_router/go_router.dart';
import '../../../core/services/storage_service.dart';
import '../../../shared/widgets/custom_textfield.dart';
import '../../../main.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  UserModel? _user;
  bool _loading = true;
  bool _savingRole = false;

  static const _roles = [
    {'value': 'patient', 'label': 'Patient', 'icon': Icons.person},
    {'value': 'clinician', 'label': 'Doctor', 'icon': Icons.local_hospital},
    {'value': 'caregiver', 'label': 'Caregiver', 'icon': Icons.favorite},
  ];

  @override
  void initState() {
    super.initState();
    _loadUser();
  }

  Future<void> _loadUser() async {
    try {
      final user = await ApiService.instance.getMe();
      if (mounted) setState(() { _user = user; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _logout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(AppLocalizations.of(context)!.logOutTitle, style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
        content: Text(AppLocalizations.of(context)!.logOutConfirm, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7))),
        backgroundColor: Theme.of(context).cardColor,
        actions: [
          TextButton(onPressed: () => context.pop(false), child: Text(AppLocalizations.of(context)!.cancel)),
          TextButton(
            onPressed: () => context.pop(true),
            child: Text(AppLocalizations.of(context)!.logOut, style: TextStyle(color: Colors.redAccent)),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    await StorageService.instance.clearTokens();
    if (mounted) context.go(Routes.login);
  }

  Future<void> _updateRole(String role) async {
    if (_savingRole) return;
    setState(() => _savingRole = true);
    try {
      await ApiService.instance.updateMe(role: role);
      final updated = await ApiService.instance.getMe();
      if (mounted) setState(() { _user = updated; _savingRole = false; });
    } catch (_) {
      if (mounted) setState(() => _savingRole = false);
    }
  }

  void _showEditPersonalInfoDialog() {
    if (_user == null) return;
    
    final nameCtrl = TextEditingController(text: _user!.fullName);
    final dobCtrl = TextEditingController(text: _user!.dateOfBirth ?? '');
    
    bool saving = false;

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: Theme.of(context).scaffoldBackgroundColor,
              title: Text(AppLocalizations.of(context)!.editPersonalInfo, style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CustomTextField(
                    controller: nameCtrl,
                    label: AppLocalizations.of(context)!.fullName,
                    icon: Icons.person_outline,
                  ),
                  SizedBox(height: 16),
                  CustomTextField(
                    controller: dobCtrl,
                    label: AppLocalizations.of(context)!.dateOfBirth,
                    icon: Icons.calendar_today,
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => ctx.pop(),
                  child: Text(AppLocalizations.of(context)!.cancel),
                ),
                FilledButton(
                  onPressed: saving ? null : () async {
                    setDialogState(() => saving = true);
                    try {
                      await ApiService.instance.updateMe(
                        fullName: nameCtrl.text.trim(),
                        dateOfBirth: dobCtrl.text.trim().isEmpty ? null : dobCtrl.text.trim(),
                      );
                      if (!ctx.mounted) return;
                      ctx.pop();
                      _loadUser(); // refresh
                    } catch (_) {
                      setDialogState(() => saving = false);
                    }
                  },
                  child: Text(saving ? 'Saving...' : 'Save'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
        centerTitle: false,
        title: Text(AppLocalizations.of(context)!.profile, style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : _user == null
              ? Center(child: Text(AppLocalizations.of(context)!.failedToLoadProfile, style: TextStyle(color: Colors.red)))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      // Initials avatar
                      CircleAvatar(
                        radius: 52,
                        backgroundColor: AppColors.primary,
                        child: Text(
                          _user!.fullName.split(' ').map((w) => w.isNotEmpty ? w[0] : '').take(2).join().toUpperCase(),
                          style: TextStyle(color: Colors.white, fontSize: 30, fontWeight: FontWeight.bold),
                        ),
                      ),
                      SizedBox(height: 18),
                      Text(
                        _user!.fullName,
                        style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 28, fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 6),
                      Text(
                        _user!.email,
                        style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70), fontSize: 16),
                      ),
                      SizedBox(height: 20),

                      // Role selector
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Theme.of(context).cardColor,
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Row(
                          children: _roles.map((r) {
                            final isActive = _user!.role == r['value'];
                            return Expanded(
                              child: GestureDetector(
                                onTap: () => _updateRole(r['value'] as String),
                                child: AnimatedContainer(
                                  duration: const Duration(milliseconds: 200),
                                  padding: const EdgeInsets.symmetric(vertical: 10),
                                  decoration: BoxDecoration(
                                    color: isActive ? AppColors.primary : Colors.transparent,
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(r['icon'] as IconData,
                                          size: 18,
                                          color: isActive ? Colors.white : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)),
                                      SizedBox(height: 4),
                                      Text(r['label'] as String,
                                          style: TextStyle(
                                              fontSize: 11,
                                              color: isActive ? Colors.white : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54),
                                              fontWeight: isActive ? FontWeight.bold : FontWeight.normal)),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                      if (_savingRole) Padding(
                        padding: EdgeInsets.only(top: 8),
                        child: Text(AppLocalizations.of(context)!.updatingRole, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 12)),
                      ),
                      SizedBox(height: 20),
                      
                      _sectionTitle('Account'),
                      SizedBox(height: 15),
                      
                      ProfileTile(
                        icon: Icons.person_outline,
                        title: AppLocalizations.of(context)!.personalInformation,
                        subtitle: AppLocalizations.of(context)!.viewEditPersonalDetails,
                        onTap: _showEditPersonalInfoDialog,
                      ),
                      ProfileTile(
                        icon: Icons.medical_information_outlined,
                        title: AppLocalizations.of(context)!.medicalProfile,
                        subtitle: AppLocalizations.of(context)!.bloodGroupAllergiesHistory,
                        onTap: () => context.push(Routes.medicalProfile),
                      ),
                      ProfileTile(
                        icon: Icons.emergency_outlined,
                        title: AppLocalizations.of(context)!.emergencyContact,
                        subtitle: AppLocalizations.of(context)!.emergencyContactInfo,
                        onTap: () => context.push(Routes.emergencyContact),
                      ),
                      
                      SizedBox(height: 30),
                      _sectionTitle('Application & Appearance'),
                      SizedBox(height: 15),
                      
                      ValueListenableBuilder<ThemeMode>(
                        valueListenable: themeModeNotifier,
                        builder: (context, mode, _) {
                          final isDark = mode == ThemeMode.dark || mode == ThemeMode.system;
                          return ProfileTile(
                            icon: isDark ? Icons.dark_mode_outlined : Icons.light_mode_outlined,
                            title: AppLocalizations.of(context)!.themeMode,
                            subtitle: isDark ? 'Dark Mode (OLED)' : 'Light Mode',
                            onTap: () async {
                              final next = isDark ? ThemeMode.light : ThemeMode.dark;
                              await StorageService.instance.setThemeMode(next);
                              themeModeNotifier.value = next;
                            },
                          );
                        },
                      ),
                      ProfileTile(
                        icon: Icons.settings_outlined,
                        title: AppLocalizations.of(context)!.settings,
                        subtitle: AppLocalizations.of(context)!.languageAndPreferences,
                        onTap: () => context.push(Routes.settings),
                      ),
                      
                      SizedBox(height: 35),
                      SizedBox(
                        width: double.infinity,
                        height: 55,
                        child: OutlinedButton.icon(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.redAccent,
                            side: BorderSide(color: Colors.redAccent.withValues(alpha: 0.4), width: 1.5),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                          ),
                          onPressed: _logout,
                          icon: Icon(Icons.logout, color: Colors.redAccent),
                          label: Text(AppLocalizations.of(context)!.logout, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.redAccent)),
                        ),
                      ),
                      SizedBox(height: 30),
                    ],
                  ),
                ),
    );
  }

  Widget _sectionTitle(String title) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(
        title,
        style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 22, fontWeight: FontWeight.bold),
      ),
    );
  }
}