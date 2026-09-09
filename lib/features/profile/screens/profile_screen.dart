import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/routing/routes.dart';
import '../../../core/services/api_models.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/storage_service.dart';
import '../../../main.dart';
import '../../../shared/widgets/custom_textfield.dart';
import '../../../shared/widgets/profile_tile.dart';

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

  static const _commonSpecialties = [
    'General Medicine',
    'Cardiology',
    'Pediatrics',
    'Neurology',
    'Dermatology',
    'Orthopedics',
    'Oncology',
    'Internal Medicine',
    'General Surgery',
    'Gynecology',
    'Psychiatry',
    'Pulmonology',
  ];

  static const _commonRelationships = [
    'Daughter',
    'Son',
    'Spouse',
    'Parent',
    'Guardian',
    'Sibling',
    'Relative',
    'Professional Caregiver',
  ];

  @override
  void initState() {
    super.initState();
    _loadUser();
  }

  Future<void> _loadUser() async {
    try {
      final user = await ApiService.instance.getMe();
      DoctorProfileModel? docProfile = user.doctorProfile;
      CaregiverProfileModel? cgProfile = user.caregiverProfile;

      docProfile ??= await StorageService.instance.getDoctorProfile(user.id);
      cgProfile ??= await StorageService.instance.getCaregiverProfile(user.id);

      final enrichedUser = user.copyWith(
        doctorProfile: docProfile,
        caregiverProfile: cgProfile,
      );

      if (mounted) {
        setState(() {
          _user = enrichedUser;
          _loading = false;
        });
      }
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
      await _loadUser();
      if (mounted) setState(() => _savingRole = false);
    } catch (_) {
      if (mounted) setState(() => _savingRole = false);
    }
  }

  String? _validateFullName(String? input) {
    final trimmed = input?.trim() ?? '';
    if (trimmed.isEmpty) {
      return 'Full name is required.';
    }
    if (!RegExp(r'[a-zA-Z]').hasMatch(trimmed)) {
      return 'Full name must contain valid letters.';
    }
    if (!RegExp(r"^[a-zA-Z\s\.\'-]+$").hasMatch(trimmed)) {
      return 'Name can only contain letters and spaces.';
    }
    return null;
  }

  String? _validateDateOfBirth(String? input) {
    if (input == null || input.trim().isEmpty) {
      return null;
    }
    final value = input.trim();
    final regExp = RegExp(r'^\d{4}-\d{2}-\d{2}$');
    if (!regExp.hasMatch(value)) {
      return 'Invalid format. Use YYYY-MM-DD (e.g., 2006-05-20)';
    }

    final parts = value.split('-');
    final year = int.parse(parts[0]);
    final month = int.parse(parts[1]);
    final day = int.parse(parts[2]);

    if (year < 1900) {
      return 'Year must be 1900 or later';
    }

    if (month < 1 || month > 12) {
      return 'Invalid month ($month). Must be between 01 and 12';
    }

    int maxDays;
    if (month == 2) {
      final bool isLeapYear = (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);
      maxDays = isLeapYear ? 29 : 28;
    } else if ([4, 6, 9, 11].contains(month)) {
      maxDays = 30;
    } else {
      maxDays = 31;
    }

    if (day < 1 || day > maxDays) {
      if (month == 2) {
        final bool isLeapYear = (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);
        return isLeapYear
            ? 'February $year (leap year) has only 29 days'
            : 'February $year has only 28 days';
      }
      return 'Month $month has only $maxDays days';
    }

    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final dobDate = DateTime(year, month, day);

    if (dobDate.isAfter(today)) {
      return 'Date of Birth cannot be in the future';
    }

    return null;
  }

  void _showEditPatientPersonalInfoDialog() {
    if (_user == null) return;
    
    final nameCtrl = TextEditingController(text: _user!.fullName);
    final dobCtrl = TextEditingController(text: _user!.dateOfBirth ?? '');
    
    bool saving = false;
    String? nameError;
    String? dobError;

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: Theme.of(context).scaffoldBackgroundColor,
              title: Text(AppLocalizations.of(context)!.editPersonalInfo, style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    CustomTextField(
                      controller: nameCtrl,
                      label: '${AppLocalizations.of(context)!.fullName} *',
                      icon: Icons.person_outline,
                      errorText: nameError,
                      onChanged: (_) {
                        if (nameError != null) setDialogState(() => nameError = null);
                      },
                    ),
                    const SizedBox(height: 16),
                    CustomTextField(
                      controller: dobCtrl,
                      label: AppLocalizations.of(context)!.dateOfBirth,
                      icon: Icons.calendar_today,
                      errorText: dobError,
                      onChanged: (_) {
                        if (dobError != null) setDialogState(() => dobError = null);
                      },
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => ctx.pop(),
                  child: Text(AppLocalizations.of(context)!.cancel),
                ),
                FilledButton(
                  onPressed: saving ? null : () async {
                    final nErr = _validateFullName(nameCtrl.text);
                    final dErr = _validateDateOfBirth(dobCtrl.text);
                    if (nErr != null || dErr != null) {
                      setDialogState(() {
                        nameError = nErr;
                        dobError = dErr;
                      });
                      return;
                    }

                    setDialogState(() {
                      saving = true;
                      nameError = null;
                      dobError = null;
                    });
                    try {
                      await ApiService.instance.updateMe(
                        fullName: nameCtrl.text.trim(),
                        dateOfBirth: dobCtrl.text.trim().isEmpty ? null : dobCtrl.text.trim(),
                      );
                      if (!ctx.mounted) return;
                      ctx.pop();
                      _loadUser();
                    } catch (e) {
                      setDialogState(() {
                        saving = false;
                        nameError = e.toString().replaceAll('Exception:', '').trim();
                      });
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

  void _showEditDoctorPersonalInfoDialog() {
    if (_user == null) return;
    final nameCtrl = TextEditingController(text: _user!.fullName);
    bool saving = false;
    String? nameError;

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: Theme.of(context).scaffoldBackgroundColor,
              title: Text('Doctor Personal Details', style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CustomTextField(
                    controller: nameCtrl,
                    label: 'Doctor Full Name *',
                    icon: Icons.person_outline,
                    errorText: nameError,
                    onChanged: (_) {
                      if (nameError != null) setDialogState(() => nameError = null);
                    },
                  ),
                ],
              ),
              actions: [
                TextButton(onPressed: () => ctx.pop(), child: Text(AppLocalizations.of(context)!.cancel)),
                FilledButton(
                  onPressed: saving ? null : () async {
                    final nErr = _validateFullName(nameCtrl.text);
                    if (nErr != null) {
                      setDialogState(() => nameError = nErr);
                      return;
                    }
                    setDialogState(() => saving = true);
                    try {
                      await ApiService.instance.updateMe(fullName: nameCtrl.text.trim());
                      if (!ctx.mounted) return;
                      ctx.pop();
                      _loadUser();
                    } catch (e) {
                      setDialogState(() {
                        saving = false;
                        nameError = e.toString().replaceAll('Exception:', '').trim();
                      });
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

  void _showEditDoctorInfoDialog() {
    if (_user == null) return;
    final doc = _user!.doctorProfile ?? const DoctorProfileModel();

    final specialtyCtrl = TextEditingController(text: doc.specialty ?? '');
    final qualCtrl = TextEditingController(text: doc.qualifications ?? '');
    final licenseCtrl = TextEditingController(text: doc.licenseNumber ?? '');
    final expCtrl = TextEditingController(text: doc.yearsOfExperience?.toString() ?? '');
    final hospitalCtrl = TextEditingController(text: doc.hospital ?? '');
    final addressCtrl = TextEditingController(text: doc.professionalAddress ?? '');

    bool saving = false;
    String? specialtyError;
    String? qualError;
    String? licenseError;
    String? expError;

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: Theme.of(context).scaffoldBackgroundColor,
              title: Text('Professional Information', style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Autocomplete<String>(
                      initialValue: TextEditingValue(text: specialtyCtrl.text),
                      optionsBuilder: (textValue) {
                        if (textValue.text.isEmpty) return _commonSpecialties;
                        return _commonSpecialties.where((s) => s.toLowerCase().contains(textValue.text.toLowerCase()));
                      },
                      onSelected: (selection) => specialtyCtrl.text = selection,
                      fieldViewBuilder: (context, controller, focusNode, onEditingComplete) {
                        return CustomTextField(
                          controller: controller,
                          label: 'Medical Specialty *',
                          icon: Icons.local_hospital_outlined,
                          errorText: specialtyError,
                          onChanged: (val) {
                            specialtyCtrl.text = val;
                            if (specialtyError != null) setDialogState(() => specialtyError = null);
                          },
                        );
                      },
                    ),
                    const SizedBox(height: 14),
                    CustomTextField(
                      controller: qualCtrl,
                      label: 'Qualifications (e.g. MBBS, MD) *',
                      icon: Icons.school_outlined,
                      errorText: qualError,
                      onChanged: (_) {
                        if (qualError != null) setDialogState(() => qualError = null);
                      },
                    ),
                    const SizedBox(height: 14),
                    CustomTextField(
                      controller: licenseCtrl,
                      label: 'Medical License / Registration No. *',
                      icon: Icons.verified_outlined,
                      errorText: licenseError,
                      onChanged: (_) {
                        if (licenseError != null) setDialogState(() => licenseError = null);
                      },
                    ),
                    const SizedBox(height: 14),
                    CustomTextField(
                      controller: expCtrl,
                      label: 'Years of Experience *',
                      icon: Icons.history_edu_outlined,
                      keyboardType: TextInputType.number,
                      errorText: expError,
                      onChanged: (_) {
                        if (expError != null) setDialogState(() => expError = null);
                      },
                    ),
                    const SizedBox(height: 14),
                    CustomTextField(
                      controller: hospitalCtrl,
                      label: 'Hospital / Clinic / Organization',
                      icon: Icons.business_outlined,
                    ),
                    const SizedBox(height: 14),
                    CustomTextField(
                      controller: addressCtrl,
                      label: 'Professional Address',
                      icon: Icons.location_on_outlined,
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(onPressed: () => ctx.pop(), child: Text(AppLocalizations.of(context)!.cancel)),
                FilledButton(
                  onPressed: saving ? null : () async {
                    final spec = specialtyCtrl.text.trim();
                    final qual = qualCtrl.text.trim();
                    final lic = licenseCtrl.text.trim();
                    final expStr = expCtrl.text.trim();
                    final expVal = int.tryParse(expStr);

                    String? sErr;
                    String? qErr;
                    String? lErr;
                    String? eErr;

                    if (spec.isEmpty) sErr = 'Medical specialty is required.';
                    if (qual.isEmpty) qErr = 'Qualifications are required.';
                    if (lic.isEmpty) lErr = 'Medical license / registration number is required.';
                    if (expStr.isEmpty || expVal == null || expVal < 0 || expVal > 70) {
                      eErr = 'Please enter valid years of experience (0 - 70).';
                    }

                    if (sErr != null || qErr != null || lErr != null || eErr != null) {
                      setDialogState(() {
                        specialtyError = sErr;
                        qualError = qErr;
                        licenseError = lErr;
                        expError = eErr;
                      });
                      return;
                    }

                    setDialogState(() => saving = true);

                    final newDocProfile = DoctorProfileModel(
                      specialty: spec,
                      qualifications: qual,
                      licenseNumber: lic,
                      yearsOfExperience: expVal,
                      hospital: hospitalCtrl.text.trim().isEmpty ? null : hospitalCtrl.text.trim(),
                      professionalAddress: addressCtrl.text.trim().isEmpty ? null : addressCtrl.text.trim(),
                    );

                    try {
                      await StorageService.instance.saveDoctorProfile(_user!.id, newDocProfile);
                      await ApiService.instance.updateMe(doctorProfile: newDocProfile);
                      if (!ctx.mounted) return;
                      ctx.pop();
                      _loadUser();
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

  void _showEditCaregiverPersonalInfoDialog() {
    if (_user == null) return;
    final nameCtrl = TextEditingController(text: _user!.fullName);
    bool saving = false;
    String? nameError;

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: Theme.of(context).scaffoldBackgroundColor,
              title: Text('Caregiver Personal Details', style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CustomTextField(
                    controller: nameCtrl,
                    label: 'Caregiver Full Name *',
                    icon: Icons.person_outline,
                    errorText: nameError,
                    onChanged: (_) {
                      if (nameError != null) setDialogState(() => nameError = null);
                    },
                  ),
                ],
              ),
              actions: [
                TextButton(onPressed: () => ctx.pop(), child: Text(AppLocalizations.of(context)!.cancel)),
                FilledButton(
                  onPressed: saving ? null : () async {
                    final nErr = _validateFullName(nameCtrl.text);
                    if (nErr != null) {
                      setDialogState(() => nameError = nErr);
                      return;
                    }
                    setDialogState(() => saving = true);
                    try {
                      await ApiService.instance.updateMe(fullName: nameCtrl.text.trim());
                      if (!ctx.mounted) return;
                      ctx.pop();
                      _loadUser();
                    } catch (e) {
                      setDialogState(() {
                        saving = false;
                        nameError = e.toString().replaceAll('Exception:', '').trim();
                      });
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

  void _showEditCaregiverInfoDialog() {
    if (_user == null) return;
    final cg = _user!.caregiverProfile ?? const CaregiverProfileModel();

    final relCtrl = TextEditingController(text: cg.relationship ?? '');
    final roleCtrl = TextEditingController(text: cg.caregiverRole ?? '');
    final patientCtrl = TextEditingController(text: cg.supportedPatientName ?? '');
    final orgCtrl = TextEditingController(text: cg.organization ?? '');

    bool saving = false;
    String? relError;

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: Theme.of(context).scaffoldBackgroundColor,
              title: Text('Caregiver Information', style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    DropdownButtonFormField<String>(
                      initialValue: _commonRelationships.contains(relCtrl.text) ? relCtrl.text : null,
                      decoration: InputDecoration(
                        labelText: 'Relationship to Patient *',
                        prefixIcon: Icon(Icons.people_outline, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6)),
                        errorText: relError,
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      items: _commonRelationships.map((r) => DropdownMenuItem(value: r, child: Text(r))).toList(),
                      onChanged: (val) {
                        if (val != null) {
                          relCtrl.text = val;
                          if (relError != null) setDialogState(() => relError = null);
                        }
                      },
                    ),
                    const SizedBox(height: 14),
                    CustomTextField(
                      controller: roleCtrl,
                      label: 'Caregiving Role (e.g. Primary Caregiver)',
                      icon: Icons.assignment_ind_outlined,
                    ),
                    const SizedBox(height: 14),
                    CustomTextField(
                      controller: patientCtrl,
                      label: 'Supported Patient Name (Optional)',
                      icon: Icons.person_search_outlined,
                    ),
                    const SizedBox(height: 14),
                    CustomTextField(
                      controller: orgCtrl,
                      label: 'Employer / Organization (Optional)',
                      icon: Icons.business_outlined,
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(onPressed: () => ctx.pop(), child: Text(AppLocalizations.of(context)!.cancel)),
                FilledButton(
                  onPressed: saving ? null : () async {
                    final rel = relCtrl.text.trim();
                    if (rel.isEmpty) {
                      setDialogState(() => relError = 'Relationship to patient is required.');
                      return;
                    }

                    setDialogState(() => saving = true);

                    final newCgProfile = CaregiverProfileModel(
                      relationship: rel,
                      caregiverRole: roleCtrl.text.trim().isEmpty ? null : roleCtrl.text.trim(),
                      supportedPatientName: patientCtrl.text.trim().isEmpty ? null : patientCtrl.text.trim(),
                      organization: orgCtrl.text.trim().isEmpty ? null : orgCtrl.text.trim(),
                    );

                    try {
                      await StorageService.instance.saveCaregiverProfile(_user!.id, newCgProfile);
                      await ApiService.instance.updateMe(caregiverProfile: newCgProfile);
                      if (!ctx.mounted) return;
                      ctx.pop();
                      _loadUser();
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
    final isPatient = _user?.role == 'patient';
    final isDoctor = _user?.role == 'clinician';
    final isCaregiver = _user?.role == 'caregiver';

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

                      // Role specific account header
                      _sectionTitle(isDoctor ? 'Doctor Account' : isCaregiver ? 'Caregiver Account' : 'Account'),
                      SizedBox(height: 15),

                      // Role specific tiles
                      if (isPatient) ...[
                        ProfileTile(
                          icon: Icons.person_outline,
                          title: AppLocalizations.of(context)!.personalInformation,
                          subtitle: AppLocalizations.of(context)!.viewEditPersonalDetails,
                          onTap: _showEditPatientPersonalInfoDialog,
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
                      ] else if (isDoctor) ...[
                        ProfileTile(
                          icon: Icons.person_outline,
                          title: AppLocalizations.of(context)!.personalInformation,
                          subtitle: 'View and edit your professional/personal details',
                          onTap: _showEditDoctorPersonalInfoDialog,
                        ),
                        ProfileTile(
                          icon: Icons.badge_outlined,
                          title: 'Professional Information',
                          subtitle: 'Specialty, qualifications and registration details',
                          onTap: _showEditDoctorInfoDialog,
                        ),
                        const SizedBox(height: 12),
                        _buildDoctorSummaryCard(),
                      ] else if (isCaregiver) ...[
                        ProfileTile(
                          icon: Icons.person_outline,
                          title: AppLocalizations.of(context)!.personalInformation,
                          subtitle: AppLocalizations.of(context)!.viewEditPersonalDetails,
                          onTap: _showEditCaregiverPersonalInfoDialog,
                        ),
                        ProfileTile(
                          icon: Icons.volunteer_activism_outlined,
                          title: 'Caregiver Information',
                          subtitle: 'Caregiving role and supported patient information',
                          onTap: _showEditCaregiverInfoDialog,
                        ),
                        const SizedBox(height: 12),
                        _buildCaregiverSummaryCard(),
                      ],

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

  Widget _buildDoctorSummaryCard() {
    final doc = _user?.doctorProfile;
    final hasInfo = doc != null && (doc.specialty?.isNotEmpty == true || doc.qualifications?.isNotEmpty == true);

    if (!hasInfo) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.amber.withValues(alpha: 0.4)),
        ),
        child: Row(
          children: [
            Icon(Icons.info_outline, color: Colors.amber.shade700),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'No professional information added yet. Tap Professional Information to complete your doctor profile.',
                style: TextStyle(fontSize: 13, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.8)),
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.local_hospital, color: AppColors.primary, size: 20),
              const SizedBox(width: 8),
              Text('Doctor Profile Summary', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 10),
          if (doc.specialty != null) Text('Specialty: ${doc.specialty}', style: TextStyle(fontSize: 13)),
          if (doc.qualifications != null) Text('Qualifications: ${doc.qualifications}', style: TextStyle(fontSize: 13)),
          if (doc.licenseNumber != null) Text('Registration No.: ${doc.licenseNumber}', style: TextStyle(fontSize: 13)),
          if (doc.yearsOfExperience != null) Text('Experience: ${doc.yearsOfExperience} years', style: TextStyle(fontSize: 13)),
          if (doc.hospital != null) Text('Hospital: ${doc.hospital}', style: TextStyle(fontSize: 13)),
        ],
      ),
    );
  }

  Widget _buildCaregiverSummaryCard() {
    final cg = _user?.caregiverProfile;
    final hasInfo = cg != null && (cg.relationship?.isNotEmpty == true);

    if (!hasInfo) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.amber.withValues(alpha: 0.4)),
        ),
        child: Row(
          children: [
            Icon(Icons.info_outline, color: Colors.amber.shade700),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'No caregiver information added yet. Tap Caregiver Information to complete your profile.',
                style: TextStyle(fontSize: 13, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.8)),
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.favorite, color: AppColors.primary, size: 20),
              const SizedBox(width: 8),
              Text('Caregiver Profile Summary', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 10),
          if (cg.relationship != null) Text('Relationship to Patient: ${cg.relationship}', style: TextStyle(fontSize: 13)),
          if (cg.caregiverRole != null) Text('Caregiving Role: ${cg.caregiverRole}', style: TextStyle(fontSize: 13)),
          if (cg.supportedPatientName != null) Text('Supporting Patient: ${cg.supportedPatientName}', style: TextStyle(fontSize: 13)),
          if (cg.organization != null) Text('Organization: ${cg.organization}', style: TextStyle(fontSize: 13)),
        ],
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