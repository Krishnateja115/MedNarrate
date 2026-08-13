import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_models.dart';
import '../../../core/routing/routes.dart';
import '../../../shared/widgets/profile_tile.dart';
import '../../../shared/widgets/custom_textfield.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  UserModel? _user;
  bool _loading = true;

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
              backgroundColor: AppColors.background,
              title: const Text('Edit Personal Info', style: TextStyle(color: Colors.white)),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CustomTextField(
                    controller: nameCtrl,
                    label: 'Full Name',
                    icon: Icons.person_outline,
                  ),
                  const SizedBox(height: 16),
                  CustomTextField(
                    controller: dobCtrl,
                    label: 'Date of Birth (YYYY-MM-DD)',
                    icon: Icons.calendar_today,
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancel'),
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
                      Navigator.pop(ctx);
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
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        centerTitle: false,
        title: const Text('Profile', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _user == null
              ? const Center(child: Text('Failed to load profile', style: TextStyle(color: Colors.red)))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      const CircleAvatar(
                        radius: 52,
                        backgroundColor: AppColors.primary,
                        child: Icon(Icons.person, color: Colors.white, size: 55),
                      ),
                      const SizedBox(height: 18),
                      Text(
                        _user!.fullName,
                        style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        _user!.email,
                        style: const TextStyle(color: Colors.white70, fontSize: 16),
                      ),
                      const SizedBox(height: 35),
                      
                      _sectionTitle('Account'),
                      const SizedBox(height: 15),
                      
                      ProfileTile(
                        icon: Icons.person_outline,
                        title: 'Personal Information',
                        subtitle: 'View and edit your personal details',
                        onTap: _showEditPersonalInfoDialog,
                      ),
                      ProfileTile(
                        icon: Icons.medical_information_outlined,
                        title: 'Medical Information',
                        subtitle: 'Blood group, allergies and history',
                        onTap: () => Navigator.pushNamed(context, Routes.medicalProfile),
                      ),
                      ProfileTile(
                        icon: Icons.emergency_outlined,
                        title: 'Emergency Contact',
                        subtitle: 'Emergency contact information',
                        onTap: () => Navigator.pushNamed(context, Routes.emergencyContact),
                      ),
                      
                      const SizedBox(height: 30),
                      _sectionTitle('Application'),
                      const SizedBox(height: 15),
                      
                      ProfileTile(
                        icon: Icons.settings,
                        title: 'Settings',
                        subtitle: 'Language, Theme & Notifications',
                        onTap: () => Navigator.pushNamed(context, Routes.settings),
                      ),
                      
                      const SizedBox(height: 35),
                      SizedBox(
                        width: double.infinity,
                        height: 55,
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.red,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                          ),
                          onPressed: () => Navigator.pushNamed(context, Routes.settings),
                          icon: const Icon(Icons.logout, color: Colors.white),
                          label: const Text('Logout', style: TextStyle(fontSize: 18, color: Colors.white)),
                        ),
                      ),
                      const SizedBox(height: 30),
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
        style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
      ),
    );
  }
}