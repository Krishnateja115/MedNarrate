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

  String? _nameError;
  String? _phoneError;
  
  bool _loading = true;
  bool _saving = false;

  static const _dummyRepeatedPhones = {
    '0000000000',
    '1111111111',
    '2222222222',
    '3333333333',
    '4444444444',
    '5555555555',
    '6666666666',
    '7777777777',
    '8888888888',
    '9999999999',
  };

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

  String? _validateName(String input) {
    final trimmed = input.trim();
    if (trimmed.isEmpty) {
      return "Please enter the emergency contact's full name.";
    }
    if (!RegExp(r'[a-zA-Z]').hasMatch(trimmed)) {
      return "Please enter a valid name containing letters.";
    }
    if (!RegExp(r"^[a-zA-Z\s\.\'-]+$").hasMatch(trimmed)) {
      return "Name can only contain letters and spaces.";
    }
    return null;
  }

  String? _validatePhone(String input) {
    final trimmed = input.trim();
    if (trimmed.isEmpty) {
      return "Please enter a valid 10-digit Indian mobile number.";
    }
    if (!RegExp(r'^[6-9]\d{9}$').hasMatch(trimmed)) {
      return "Please enter a valid 10-digit Indian mobile number.";
    }
    if (_dummyRepeatedPhones.contains(trimmed)) {
      return "Please enter a valid 10-digit Indian mobile number.";
    }
    return null;
  }

  Future<void> _save() async {
    setState(() {
      _nameError = null;
      _phoneError = null;
    });

    final nameVal = _nameController.text.trim();
    final phoneVal = _phoneController.text.trim();

    final nameErr = _validateName(nameVal);
    final phoneErr = _validatePhone(phoneVal);

    if (nameErr != null || phoneErr != null) {
      setState(() {
        _nameError = nameErr;
        _phoneError = phoneErr;
      });
      return;
    }

    setState(() => _saving = true);

    try {
      await ApiService.instance.updateMe(
        emergencyContactName: nameVal,
        emergencyContactPhone: phoneVal,
      );

      if (!mounted) return;

      Helpers.showSuccess(context, 'Emergency contact saved successfully.');
      context.pop();
    } on ApiException catch (e) {
      if (mounted) Helpers.showError(context, e.message);
    } catch (_) {
      if (mounted) Helpers.showError(context, 'Failed to save emergency contact.');
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
                      errorText: _nameError,
                      onChanged: (_) {
                        if (_nameError != null) setState(() => _nameError = null);
                      },
                    ),
                    SizedBox(height: 20),
                    CustomTextField(
                      controller: _phoneController,
                      label: AppLocalizations.of(context)!.phoneNumber,
                      icon: Icons.phone_outlined,
                      keyboardType: TextInputType.phone,
                      errorText: _phoneError,
                      onChanged: (_) {
                        if (_phoneError != null) setState(() => _phoneError = null);
                      },
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