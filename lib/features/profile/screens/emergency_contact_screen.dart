import 'package:flutter/material.dart';

import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/helpers.dart';
import '../../../shared/widgets/custom_textfield.dart';
import 'package:go_router/go_router.dart';
import '../../../shared/widgets/primary_button.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

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
    _nameController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text(AppLocalizations.of(context)!.emergencyContact),
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(height: 15),
                    Text(AppLocalizations.of(context)!.emergencyContact,
                      style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.onSurface),
                    ),
                    SizedBox(height: 10),
                    Text(AppLocalizations.of(context)!.emergencyContactSubtitle,
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
                    ),
                    SizedBox(height: 35),
                    CustomTextField(
                      controller: _nameController,
                      label: AppLocalizations.of(context)!.fullName,
                      icon: Icons.person_outline,
                    ),
                    SizedBox(height: 20),
                    CustomTextField(
                      controller: _phoneController,
                      label: AppLocalizations.of(context)!.phoneNumber,
                      icon: Icons.phone_outlined,
                      keyboardType: TextInputType.phone,
                    ),
                    SizedBox(height: 40),
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