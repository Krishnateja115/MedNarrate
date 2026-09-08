import 'package:flutter/material.dart';

import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/helpers.dart';
import '../../../shared/widgets/custom_textfield.dart';
import 'package:go_router/go_router.dart';
import '../../../shared/widgets/primary_button.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class MedicalProfileScreen extends StatefulWidget {
  const MedicalProfileScreen({super.key});

  @override
  State<MedicalProfileScreen> createState() => _MedicalProfileScreenState();
}

class _MedicalProfileScreenState extends State<MedicalProfileScreen> {
  final _bloodController = TextEditingController();
  final _allergiesController = TextEditingController();
  final _conditionsController = TextEditingController();
  
  String? _bloodError;
  String? _allergiesError;
  String? _conditionsError;

  bool _loading = true;
  bool _saving = false;

  static const _validBloodGroups = {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'};

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

  String? _validateBloodGroup(String input) {
    final trimmed = input.trim();
    if (trimmed.isEmpty) return null; // Optional

    final normalized = trimmed.toUpperCase();
    if (!_validBloodGroups.contains(normalized)) {
      return 'Invalid blood group. Valid options: A+, A-, B+, B-, AB+, AB-, O+, O-';
    }
    return null;
  }

  String? _validateTextField(String input, String fieldName) {
    final trimmed = input.trim();
    if (trimmed.isEmpty) return null; // Optional

    // Check if input consists solely of special characters/punctuation (no alphanumeric letters or numbers)
    final hasAlphaNum = RegExp(r'[a-zA-Z0-9]').hasMatch(trimmed);
    if (!hasAlphaNum) {
      return '$fieldName cannot consist only of special characters.';
    }
    return null;
  }

  Future<void> _save() async {
    setState(() {
      _bloodError = null;
      _allergiesError = null;
      _conditionsError = null;
    });

    final rawBlood = _bloodController.text.trim();
    final allergiesVal = _allergiesController.text.trim();
    final conditionsVal = _conditionsController.text.trim();

    // 1. Validate fields for INVALID data
    final bloodErr = _validateBloodGroup(rawBlood);
    final allergiesErr = _validateTextField(allergiesVal, 'Known Allergies');
    final conditionsErr = _validateTextField(conditionsVal, 'Chronic Conditions');

    if (bloodErr != null || allergiesErr != null || conditionsErr != null) {
      setState(() {
        _bloodError = bloodErr;
        _allergiesError = allergiesErr;
        _conditionsError = conditionsErr;
      });
      return; // DO NOT SAVE if invalid data is present
    }

    // Normalize blood group to uppercase (e.g. "o+" -> "O+")
    final normalizedBlood = rawBlood.isNotEmpty ? rawBlood.toUpperCase() : '';

    setState(() => _saving = true);

    try {
      await ApiService.instance.updateMe(
        bloodGroup: normalizedBlood,
        knownAllergies: allergiesVal,
        chronicConditions: conditionsVal,
      );

      if (!mounted) return;

      _bloodController.text = normalizedBlood;

      // 2. Check for MISSING (empty) optional fields
      final missingFields = <String>[];
      if (normalizedBlood.isEmpty) missingFields.add('Blood Group');
      if (allergiesVal.isEmpty) missingFields.add('Known Allergies');
      if (conditionsVal.isEmpty) missingFields.add('Chronic Conditions');

      if (missingFields.isNotEmpty) {
        final missingDetails = missingFields.map((f) => '$f has not been provided.').join(' ');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: Colors.amber.shade900,
            duration: const Duration(seconds: 4),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Some medical information is incomplete. You can update it later.',
                  style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 4),
                Text(
                  missingDetails,
                  style: const TextStyle(fontSize: 12, color: Colors.white70),
                ),
              ],
            ),
          ),
        );
      } else {
        Helpers.showSuccess(context, 'Medical information saved successfully.');
      }

      context.pop();
    } on ApiException catch (e) {
      if (mounted) Helpers.showError(context, e.message);
    } catch (_) {
      if (mounted) Helpers.showError(context, 'Failed to save medical information');
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
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text(AppLocalizations.of(context)!.medicalProfile),
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(height: 10),
                  Text(AppLocalizations.of(context)!.keepMedicalHistoryUpdated,
                    style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70), fontSize: 16),
                  ),
                  SizedBox(height: 35),
                  CustomTextField(
                    controller: _bloodController,
                    label: AppLocalizations.of(context)!.bloodGroup,
                    icon: Icons.bloodtype_outlined,
                    errorText: _bloodError,
                    onChanged: (_) {
                      if (_bloodError != null) setState(() => _bloodError = null);
                    },
                  ),
                  SizedBox(height: 20),
                  CustomTextField(
                    controller: _allergiesController,
                    label: AppLocalizations.of(context)!.knownAllergies,
                    icon: Icons.warning_amber_outlined,
                    errorText: _allergiesError,
                    onChanged: (_) {
                      if (_allergiesError != null) setState(() => _allergiesError = null);
                    },
                  ),
                  SizedBox(height: 20),
                  CustomTextField(
                    controller: _conditionsController,
                    label: AppLocalizations.of(context)!.chronicConditions,
                    icon: Icons.local_hospital_outlined,
                    errorText: _conditionsError,
                    onChanged: (_) {
                      if (_conditionsError != null) setState(() => _conditionsError = null);
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
    );
  }
}