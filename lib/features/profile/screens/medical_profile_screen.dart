import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/helpers.dart';
import '../../../shared/widgets/custom_textfield.dart';
import 'package:go_router/go_router.dart';
import '../../../shared/widgets/primary_button.dart';

class MedicalProfileScreen extends StatefulWidget {
  const MedicalProfileScreen({super.key});

  @override
  State<MedicalProfileScreen> createState() => _MedicalProfileScreenState();
}

class _MedicalProfileScreenState extends State<MedicalProfileScreen> {
  final _bloodController = TextEditingController();
  final _allergiesController = TextEditingController();
  final _conditionsController = TextEditingController();
  
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
          _bloodController.text = user.medicalProfile?.bloodGroup ?? '';
          _allergiesController.text = user.medicalProfile?.knownAllergies ?? '';
          _conditionsController.text = user.medicalProfile?.chronicConditions ?? '';
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
        bloodGroup: _bloodController.text.trim(),
        knownAllergies: _allergiesController.text.trim(),
        chronicConditions: _conditionsController.text.trim(),
      );
      if (mounted) {
        Helpers.showSuccess(context, 'Medical profile updated');
        context.pop();
      }
    } on ApiException catch (e) {
      if (mounted) Helpers.showError(context, e.message);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    _bloodController.dispose();
    _allergiesController.dispose();
    _conditionsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Medical Information'),
        backgroundColor: AppColors.background,
        elevation: 0,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 10),
                  const Text(
                    "Keep your medical history up to date for better analysis.",
                    style: TextStyle(color: Colors.white70, fontSize: 16),
                  ),
                  const SizedBox(height: 35),
                  CustomTextField(
                    controller: _bloodController,
                    label: 'Blood Group',
                    icon: Icons.bloodtype_outlined,
                  ),
                  const SizedBox(height: 20),
                  CustomTextField(
                    controller: _allergiesController,
                    label: 'Known Allergies',
                    icon: Icons.warning_amber_outlined,
                  ),
                  const SizedBox(height: 20),
                  CustomTextField(
                    controller: _conditionsController,
                    label: 'Chronic Conditions',
                    icon: Icons.local_hospital_outlined,
                  ),
                  const SizedBox(height: 40),
                  PrimaryButton(
                    text: _saving ? 'Saving...' : 'Save',
                    onPressed: _saving ? null : () { _save(); },
                  ),
                ],
              ),
            ),
    );
  }
}