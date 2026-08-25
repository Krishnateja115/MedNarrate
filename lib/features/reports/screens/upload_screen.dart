
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/utils/report_polling.dart';
import 'package:go_router/go_router.dart';
import '../../../core/routing/routes.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleCtrl = TextEditingController();
  final _hospitalCtrl = TextEditingController();

  PlatformFile? _selectedFile;
  String _reportType = 'blood';
  DateTime _reportDate = DateTime.now();
  bool _uploading = false;
  bool _processing = false;
  String? _errorMessage;

  static const _maxSizeMb = 25;
  static const _validExtensions = ['pdf', 'jpg', 'jpeg', 'png'];
  static const _reportTypes = ['blood', 'pathology', 'health', 'other'];

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: _validExtensions,
    );
    if (result == null || result.files.isEmpty) return;
    final file = result.files.first;
    final ext = file.extension?.toLowerCase() ?? '';
    if (!_validExtensions.contains(ext)) {
      setState(() => _errorMessage = 'Only PDF, JPG, JPEG, PNG are allowed.');
      return;
    }
    final sizeMb = (file.size) / (1024 * 1024);
    if (sizeMb > _maxSizeMb) {
      setState(() => _errorMessage = 'File must be smaller than ${Formatters.formatFileSize(_maxSizeMb * 1024 * 1024)}.');
      return;
    }
    setState(() { _selectedFile = file; _errorMessage = null; });
  }

  Future<void> _upload() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedFile?.path == null) {
      setState(() => _errorMessage = 'Please select a file.');
      return;
    }
    setState(() { _uploading = true; _errorMessage = null; });
    try {
      final report = await ApiService.instance.uploadReport(
        file: _selectedFile!,
        title: _titleCtrl.text.trim(),
        hospital: _hospitalCtrl.text.trim().isEmpty ? null : _hospitalCtrl.text.trim(),
        reportDate: '${_reportDate.year}-${_reportDate.month.toString().padLeft(2, '0')}-${_reportDate.day.toString().padLeft(2, '0')}',
        reportType: _reportType,
      );
      if (!mounted) return;
      // Trigger analysis
      setState(() { _uploading = false; _processing = true; });
      await ApiService.instance.processReport(report.id);
      // Poll until done
      await for (final status in pollReportStatus(report.id)) {
        if (!mounted) return;
        if (status.processingStatus == 'completed') {
          setState(() => _processing = false);
          Helpers.showSuccess(context, AppLocalizations.of(context)!.reportAnalyzedSuccessfully);
          context.go(Routes.reportAnalysis, extra: report.id);
          return;
        } else if (status.processingStatus == 'failed') {
          setState(() { _processing = false; _errorMessage = status.errorReason ?? 'Analysis failed.'; });
          return;
        }
      }
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() { _uploading = false; _processing = false; _errorMessage = e.message; });
    }
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _hospitalCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
        title: Text(AppLocalizations.of(context)!.uploadReport),
      ),
      body: _processing
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(),
                  SizedBox(height: 24),
                  Text(AppLocalizations.of(context)!.analyzingReport,
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70))),
                  SizedBox(height: 8),
                  Text(AppLocalizations.of(context)!.thisMayTakeAMinute,
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 13)),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Form(
                key: _formKey,
                child: Column(
                  children: [
                    Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.onSurface.withValues(alpha: .06),
                        shape: BoxShape.circle,
                        border: Border.all(color: AppColors.border, width: 1),
                      ),
                      child: Icon(Icons.upload_file_rounded, color: Theme.of(context).colorScheme.onSurface, size: 48),
                    ),
                    SizedBox(height: 24),
                    Text(AppLocalizations.of(context)!.uploadMedicalReport,
                        style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.onSurface)),
                    SizedBox(height: 6),
                    Text(AppLocalizations.of(context)!.pdfJpgPngMax,
                        style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 13)),
                    SizedBox(height: 28),
                    // Title
                    TextFormField(
                      controller: _titleCtrl,
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
                      decoration: _inputDec('Title', Icons.title),
                      validator: (v) => v == null || v.trim().isEmpty ? 'Title is required' : null,
                    ),
                    SizedBox(height: 16),
                    // Hospital (optional)
                    TextFormField(
                      controller: _hospitalCtrl,
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
                      decoration: _inputDec('Hospital (optional)', Icons.local_hospital_outlined),
                    ),
                    SizedBox(height: 16),
                    // Report type
                    DropdownButtonFormField<String>(
                      initialValue: _reportType,
                      dropdownColor: Theme.of(context).cardColor,
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
                      decoration: _inputDec('Report Type', Icons.category_outlined),
                      items: _reportTypes.map((t) => DropdownMenuItem(
                        value: t,
                        child: Text(Helpers.reportTypeLabel(t),
                            style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
                      )).toList(),
                      onChanged: (v) => setState(() => _reportType = v!),
                    ),
                    SizedBox(height: 16),
                    // Date picker
                    GestureDetector(
                      onTap: () async {
                        final picked = await showDatePicker(
                          context: context,
                          initialDate: _reportDate,
                          firstDate: DateTime(2000),
                          lastDate: DateTime.now(),
                        );
                        if (picked != null) setState(() => _reportDate = picked);
                      },
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Theme.of(context).cardColor,
                          border: Border.all(color: AppColors.border),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.calendar_today, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), size: 20),
                            SizedBox(width: 12),
                            Text('Report Date: ${Formatters.formatDate(_reportDate)}',
                                style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 15)),
                          ],
                        ),
                      ),
                    ),
                    SizedBox(height: 24),
                    // File picker
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: OutlinedButton.icon(
                        onPressed: _uploading ? null : _pickFile,
                        icon: Icon(Icons.attach_file_rounded, color: _selectedFile != null ? Theme.of(context).colorScheme.onSurface : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
                        label: Text(
                          _selectedFile == null ? 'Choose File' : _selectedFile!.name,
                          style: TextStyle(
                            color: _selectedFile != null ? Theme.of(context).colorScheme.onSurface : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        style: OutlinedButton.styleFrom(
                          side: BorderSide(color: _selectedFile != null ? Theme.of(context).colorScheme.onSurface : AppColors.border, width: 1.5),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          backgroundColor: _selectedFile != null ? Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.08) : Colors.transparent,
                        ),
                      ),
                    ),
                    if (_selectedFile != null) ...[
                      SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Theme.of(context).cardColor,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: AppColors.border, width: 1),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.insert_drive_file_outlined, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
                            SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(_selectedFile!.name, style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontWeight: FontWeight.w600)),
                                  Text(Formatters.formatFileSize(_selectedFile!.size), style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 12)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                    if (_errorMessage != null) ...[
                      SizedBox(height: 16),
                      Text(_errorMessage!, style: TextStyle(color: Colors.redAccent)),
                    ],
                    SizedBox(height: 32),
                    SizedBox(
                      width: double.infinity,
                      height: 55,
                      child: FilledButton(
                        style: FilledButton.styleFrom(
                          backgroundColor: Theme.of(context).colorScheme.primary,
                                    foregroundColor: Colors.white,
                          disabledBackgroundColor: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.12),
                          disabledForegroundColor: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.30),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                        onPressed: (_uploading || _selectedFile == null) ? null : _upload,
                        child: Text(
                          _uploading ? 'Uploading…' : 'Upload & Analyze',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  InputDecoration _inputDec(String label, IconData icon) => InputDecoration(
    labelText: label,
    labelStyle: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
    prefixIcon: Icon(icon, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)),
    filled: true,
    fillColor: Theme.of(context).cardColor,
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide(color: AppColors.border),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide(color: Theme.of(context).colorScheme.onSurface, width: 1.5),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide(color: Colors.redAccent),
    ),
    focusedErrorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide(color: Colors.redAccent),
    ),
  );
}