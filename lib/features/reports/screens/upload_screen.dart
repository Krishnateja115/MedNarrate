
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
          Helpers.showSuccess(context, 'Report analyzed successfully!');
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
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text('Upload Report'),
      ),
      body: _processing
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 24),
                  const Text('Analyzing your report with AI…',
                      style: TextStyle(color: Colors.white70)),
                  const SizedBox(height: 8),
                  const Text('This may take a minute.',
                      style: TextStyle(color: Colors.white54, fontSize: 13)),
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
                        color: Colors.white.withValues(alpha: .06),
                        shape: BoxShape.circle,
                        border: Border.all(color: AppColors.border, width: 1),
                      ),
                      child: const Icon(Icons.upload_file_rounded, color: Colors.white, size: 48),
                    ),
                    const SizedBox(height: 24),
                    const Text('Upload Medical Report',
                        style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
                    const SizedBox(height: 6),
                    const Text('PDF, JPG, JPEG, or PNG · max 25 MB',
                        style: TextStyle(color: Colors.white54, fontSize: 13)),
                    const SizedBox(height: 28),
                    // Title
                    TextFormField(
                      controller: _titleCtrl,
                      style: const TextStyle(color: Colors.white),
                      decoration: _inputDec('Title', Icons.title),
                      validator: (v) => v == null || v.trim().isEmpty ? 'Title is required' : null,
                    ),
                    const SizedBox(height: 16),
                    // Hospital (optional)
                    TextFormField(
                      controller: _hospitalCtrl,
                      style: const TextStyle(color: Colors.white),
                      decoration: _inputDec('Hospital (optional)', Icons.local_hospital_outlined),
                    ),
                    const SizedBox(height: 16),
                    // Report type
                    DropdownButtonFormField<String>(
                      initialValue: _reportType,
                      dropdownColor: AppColors.card,
                      style: const TextStyle(color: Colors.white),
                      decoration: _inputDec('Report Type', Icons.category_outlined),
                      items: _reportTypes.map((t) => DropdownMenuItem(
                        value: t,
                        child: Text(Helpers.reportTypeLabel(t),
                            style: const TextStyle(color: Colors.white)),
                      )).toList(),
                      onChanged: (v) => setState(() => _reportType = v!),
                    ),
                    const SizedBox(height: 16),
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
                          color: AppColors.card,
                          border: Border.all(color: AppColors.border),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.calendar_today, color: Colors.white54, size: 20),
                            const SizedBox(width: 12),
                            Text('Report Date: ${Formatters.formatDate(_reportDate)}',
                                style: const TextStyle(color: Colors.white, fontSize: 15)),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    // File picker
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: OutlinedButton.icon(
                        onPressed: _uploading ? null : _pickFile,
                        icon: Icon(Icons.attach_file_rounded, color: _selectedFile != null ? Colors.white : Colors.white70),
                        label: Text(
                          _selectedFile == null ? 'Choose File' : _selectedFile!.name,
                          style: TextStyle(
                            color: _selectedFile != null ? Colors.white : Colors.white70,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        style: OutlinedButton.styleFrom(
                          side: BorderSide(color: _selectedFile != null ? Colors.white : AppColors.border, width: 1.5),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          backgroundColor: _selectedFile != null ? Colors.white.withValues(alpha: 0.08) : Colors.transparent,
                        ),
                      ),
                    ),
                    if (_selectedFile != null) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.card,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: AppColors.border, width: 1),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.insert_drive_file_outlined, color: Colors.white70),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(_selectedFile!.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                                  Text(Formatters.formatFileSize(_selectedFile!.size), style: const TextStyle(color: Colors.white54, fontSize: 12)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                    if (_errorMessage != null) ...[
                      const SizedBox(height: 16),
                      Text(_errorMessage!, style: const TextStyle(color: Colors.redAccent)),
                    ],
                    const SizedBox(height: 32),
                    SizedBox(
                      width: double.infinity,
                      height: 55,
                      child: FilledButton(
                        style: FilledButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: Colors.black,
                          disabledBackgroundColor: Colors.white12,
                          disabledForegroundColor: Colors.white30,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                        onPressed: (_uploading || _selectedFile == null) ? null : _upload,
                        child: Text(
                          _uploading ? 'Uploading…' : 'Upload & Analyze',
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
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
    labelStyle: const TextStyle(color: Colors.white70),
    prefixIcon: Icon(icon, color: Colors.white54),
    filled: true,
    fillColor: AppColors.card,
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: const BorderSide(color: AppColors.border),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: const BorderSide(color: Colors.white, width: 1.5),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: const BorderSide(color: Colors.redAccent),
    ),
    focusedErrorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: const BorderSide(color: Colors.redAccent),
    ),
  );
}