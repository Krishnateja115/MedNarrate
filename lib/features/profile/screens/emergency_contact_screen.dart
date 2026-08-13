import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/helpers.dart';
import '../../../shared/widgets/custom_textfield.dart';
import '../../../shared/widgets/primary_button.dart';

class EmergencyContactScreen extends StatefulWidget {
  const EmergencyContactScreen({super.key});

  @override
  State<EmergencyContactScreen> createState() => _EmergencyContactScreenState();
}

class _EmergencyContactScreenState extends State<EmergencyContactScreen> {
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final user = await ApiService.instance.getMe();
      if (mounted) {
        setState(() {
          _nameController.text = user.medicalProfile?.emergencyContactName ?? '';
          _phoneController.text = user.medicalProfile?.emergencyContactPhone ?? '';
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await ApiService.instance.updateMe(
        emergencyContactName: _nameController.text.trim(),
        emergencyContactPhone: _phoneController.text.trim(),
      );
      if (mounted) {
        Helpers.showSuccess(context, 'Emergency contact updated');
        Navigator.pop(context);
      }
    } on ApiException catch (e) {
      if (mounted) Helpers.showError(context, e.message);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Emergency Contact'),
        backgroundColor: AppColors.background,
        elevation: 0,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 15),
                    const Text(
                      'Emergency Contact',
                      style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      "We'll use this only during emergencies.",
                      style: TextStyle(color: Colors.white70),
                    ),
                    const SizedBox(height: 35),
                    CustomTextField(
                      controller: _nameController,
                      label: 'Full Name',
                      icon: Icons.person_outline,
                    ),
                    const SizedBox(height: 20),
                    CustomTextField(
                      controller: _phoneController,
                      label: 'Phone Number',
                      icon: Icons.phone_outlined,
                      keyboardType: TextInputType.phone,
                    ),
                    const SizedBox(height: 40),
                    PrimaryButton(
                      text: _saving ? 'Saving...' : 'Save',
                      onPressed: _saving ? null : () { _save(); },
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}