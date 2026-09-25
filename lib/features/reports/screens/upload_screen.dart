import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:shimmer/shimmer.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/routing/routes.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/api_service.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/utils/helpers.dart';
import '../../../core/utils/report_polling.dart';
import 'package:mednarrate/l10n/app_localizations.dart';
import 'reports_screen.dart';
import '../../dashboard/screens/dashboard_screen.dart';

enum UploadStep {
  idle,          // Initial state: Form ready, no file selected
  fileSelected,  // File selected: File card visible, ready to submit
  uploading,     // Uploading bytes to backend
  processing,    // Backend text extraction / ML / AI analysis
  failed,        // Analysis or upload failed
  success,       // Processing succeeded
}

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleCtrl = TextEditingController();
  final _hospitalCtrl = TextEditingController();

  UploadStep _step = UploadStep.idle;
  PlatformFile? _selectedFile;
  String _reportType = 'blood';
  DateTime? _reportDate;
  bool _customDateSelected = false;

  String? _errorMessage;
  String? _failureCategory;
  String? _createdReportId;
  String _processingStatusText = 'Uploading report...';

  static const _maxSizeMb = 25;
  static const _validExtensions = ['pdf', 'jpg', 'jpeg', 'png'];
  static const _reportTypes = ['blood', 'pathology', 'health', 'other'];

  @override
  void dispose() {
    _titleCtrl.dispose();
    _hospitalCtrl.dispose();
    super.dispose();
  }

  void _clearError() {
    if (_errorMessage != null) {
      setState(() => _errorMessage = null);
    }
  }

  void _clearFile() {
    setState(() {
      _selectedFile = null;
      _errorMessage = null;
      _failureCategory = null;
      _createdReportId = null;
      _step = UploadStep.idle;
      _titleCtrl.clear();
      _hospitalCtrl.clear();
      _reportDate = null;
      _customDateSelected = false;
      _reportType = 'blood';
    });
  }

  Future<void> _pickFile() async {
    _clearError();
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: _validExtensions,
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;

    final file = result.files.first;
    final ext = file.extension?.toLowerCase() ?? '';
    if (!_validExtensions.contains(ext)) {
      setState(() {
        _errorMessage = 'Only PDF, JPG, JPEG, and PNG files are supported.';
        _step = UploadStep.idle;
      });
      return;
    }

    final sizeMb = (file.size) / (1024 * 1024);
    if (sizeMb > _maxSizeMb) {
      setState(() {
        _errorMessage = 'File must be smaller than ${Formatters.formatFileSize(_maxSizeMb * 1024 * 1024)}.';
        _step = UploadStep.idle;
      });
      return;
    }

    setState(() {
      _selectedFile = file;
      _errorMessage = null;
      _createdReportId = null;
      _step = UploadStep.fileSelected;

      // Auto-suggest title if empty
      if (_titleCtrl.text.trim().isEmpty) {
        final rawName = file.name.replaceAll(RegExp(r'\.[^/.]+$'), '');
        final cleanTitle = rawName.replaceAll(RegExp(r'[_-]'), ' ').trim();
        if (cleanTitle.isNotEmpty) {
          _titleCtrl.text = cleanTitle[0].toUpperCase() + cleanTitle.substring(1);
        }
      }
    });
  }

  String _sanitizeError(String? rawError, {String? category}) {
    final cat = category ?? _failureCategory;
    if (cat == 'OCR_ENGINE_UNAVAILABLE') {
      return 'The report was uploaded successfully, but text recognition is not available on this server.';
    }
    if (cat == 'OCR_NO_MEANINGFUL_TEXT' || cat == 'OCR_FAILED' || cat == 'IMAGE_DECODE_ERROR') {
      return 'The image was uploaded successfully, but readable medical text could not be extracted from it. Please upload a clearer scan or image.';
    }
    if (cat == 'PDF_EXTRACTION_ERROR' || cat == 'CORRUPT_PDF' || cat == 'UNREADABLE_PDF') {
      return 'Unable to extract text from this PDF document. The file may be scanned or unreadable.';
    }
    if (cat == 'FILE_INVALID' || cat == 'EMPTY_FILE') {
      return 'The uploaded file is empty or formatted improperly.';
    }
    if (cat == 'LLM_UNAVAILABLE' || cat == 'LLM_GENERATION_ERROR' || cat == 'LLM_NOT_CONFIGURED') {
      return 'Your report was uploaded and text was extracted, but AI analysis could not be completed right now.';
    }

    if (rawError == null || rawError.trim().isEmpty) {
      return 'Your report was uploaded successfully, but AI analysis could not be completed right now.';
    }
    final lower = rawError.toLowerCase();
    if (lower.contains('ocr engine') || lower.contains('tesseract ocr engine is unavailable') || lower.contains('not available on this server')) {
      return 'The report was uploaded successfully, but text recognition is not available on this server.';
    }
    if (lower.contains('unable to read') || lower.contains('could not extract') || lower.contains('ocr')) {
      return 'The image was uploaded successfully, but readable medical text could not be extracted from it. Please upload a clearer scan or image.';
    }
    if (lower.contains('gemini_api_key') ||
        lower.contains('ollama_url') ||
        lower.contains('vertex_project_id') ||
        lower.contains('service configuration') ||
        lower.contains('ai service') ||
        lower.contains('llmconfigurationerror') ||
        lower.contains('runtimeerror') ||
        lower.contains('provider credentials') ||
        lower.contains('model') ||
        lower.contains('gemini')) {
      return 'Your report was uploaded and text was extracted, but AI analysis could not be completed right now.';
    }
    if (lower.contains('socketexception') || lower.contains('connection') || lower.contains('network')) {
      return 'Unable to connect to the server. Please check your network connection.';
    }
    if (lower.contains('unauthorized') || lower.contains('401') || lower.contains('session')) {
      return 'Your session has expired. Please sign in again.';
    }
    return rawError;
  }

  Future<void> _uploadAndAnalyze() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedFile == null) {
      setState(() => _errorMessage = 'Please select a report file first.');
      return;
    }

    setState(() {
      _step = UploadStep.uploading;
      _errorMessage = null;
      _processingStatusText = 'Uploading medical report...';
    });

    final targetDate = _reportDate ?? DateTime.now();
    final dateStr = '${targetDate.year}-${targetDate.month.toString().padLeft(2, '0')}-${targetDate.day.toString().padLeft(2, '0')}';

    try {
      final report = await ApiService.instance.uploadReport(
        file: _selectedFile!,
        title: _titleCtrl.text.trim(),
        hospital: _hospitalCtrl.text.trim().isEmpty ? null : _hospitalCtrl.text.trim(),
        reportDate: dateStr,
        reportType: _reportType,
      );

      if (!mounted) return;
      _createdReportId = report.id;

      setState(() {
        _step = UploadStep.processing;
        _processingStatusText = 'Extracting text and analyzing report...';
      });

      await ApiService.instance.processReport(report.id);

      await for (final status in pollReportStatus(report.id)) {
        if (!mounted) return;
        if (status.processingStatus == 'completed') {
          setState(() => _step = UploadStep.success);
          final loc = AppLocalizations.of(context);
          final msg = loc != null ? loc.reportAnalyzedSuccessfully : 'Report analyzed successfully!';
          Helpers.showSuccess(context, msg);
          
          ReportsScreen.onRefreshRequested?.call();
          DashboardScreen.onRefreshRequested?.call();
          
          context.pushReplacement(Routes.reportDetails, extra: report.id);
          return;
        } else if (status.processingStatus == 'failed') {
          setState(() {
            _step = UploadStep.failed;
            _failureCategory = status.failureCategory;
            _errorMessage = _sanitizeError(status.errorReason, category: status.failureCategory);
          });
          return;
        }
      }
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _step = UploadStep.failed;
        _errorMessage = _sanitizeError(e.message);
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _step = UploadStep.failed;
        _errorMessage = _sanitizeError(e.toString());
      });
    }
  }

  Future<void> _retryAnalysis() async {
    if (_createdReportId == null) {
      await _uploadAndAnalyze();
      return;
    }

    setState(() {
      _step = UploadStep.processing;
      _errorMessage = null;
      _processingStatusText = 'Retrying AI analysis...';
    });

    try {
      await ApiService.instance.processReport(_createdReportId!, force: true);

      await for (final status in pollReportStatus(_createdReportId!)) {
        if (!mounted) return;
        if (status.processingStatus == 'completed') {
          setState(() => _step = UploadStep.success);
          final loc = AppLocalizations.of(context);
          final msg = loc != null ? loc.reportAnalyzedSuccessfully : 'Report analyzed successfully!';
          Helpers.showSuccess(context, msg);
          
          ReportsScreen.onRefreshRequested?.call();
          DashboardScreen.onRefreshRequested?.call();
          
          context.pushReplacement(Routes.reportDetails, extra: _createdReportId);
          return;
        } else if (status.processingStatus == 'failed') {
          setState(() {
            _step = UploadStep.failed;
            _failureCategory = status.failureCategory;
            _errorMessage = _sanitizeError(status.errorReason, category: status.failureCategory);
          });
          return;
        }
      }
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _step = UploadStep.failed;
        _errorMessage = _sanitizeError(e.message);
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _step = UploadStep.failed;
        _errorMessage = _sanitizeError(e.toString());
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isProcessing = _step == UploadStep.uploading || _step == UploadStep.processing;
    final loc = AppLocalizations.of(context);
    final isReportSavedAndFailed = _step == UploadStep.failed && _createdReportId != null;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: theme.scaffoldBackgroundColor,
        elevation: 0,
        title: Text(loc?.uploadReport ?? 'Upload Medical Report'),
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Page Header
                  _buildHeader(theme, loc),
                  const SizedBox(height: 24),

                  // Title Field
                  TextFormField(
                    controller: _titleCtrl,
                    style: TextStyle(color: theme.colorScheme.onSurface),
                    decoration: _inputDec('Report Title *', Icons.title_rounded, hint: 'e.g. Annual Blood Test'),
                    validator: (v) => v == null || v.trim().isEmpty ? 'Title is required' : null,
                  ),
                  const SizedBox(height: 16),

                  // Hospital Field
                  TextFormField(
                    controller: _hospitalCtrl,
                    style: TextStyle(color: theme.colorScheme.onSurface),
                    decoration: _inputDec('Hospital / Clinic (optional)', Icons.local_hospital_outlined, hint: 'e.g. City General Hospital'),
                  ),
                  const SizedBox(height: 16),

                  // Responsive Grid for Report Type & Report Date
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final isWide = constraints.maxWidth >= 550;
                      if (isWide) {
                        return Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(child: _buildReportTypeDropdown(theme)),
                            const SizedBox(width: 16),
                            Expanded(child: _buildDatePickerTile(theme)),
                          ],
                        );
                      }
                      return Column(
                        children: [
                          _buildReportTypeDropdown(theme),
                          const SizedBox(height: 16),
                          _buildDatePickerTile(theme),
                        ],
                      );
                    },
                  ),
                  const SizedBox(height: 24),

                  // File Picker / Selected File Area
                  _buildFileArea(theme),
                  const SizedBox(height: 20),

                  // Status Stepper Indicator (shown when report is saved)
                  if (_createdReportId != null) ...[
                    _buildUploadStatusIndicator(theme),
                    const SizedBox(height: 20),
                  ],

                  // Active Processing Card
                  if (isProcessing) ...[
                    _buildProcessingCard(theme),
                    const SizedBox(height: 20),
                  ],

                  // Failed Analysis Error Container
                  if (_step == UploadStep.failed && _errorMessage != null) ...[
                    _buildErrorCard(theme),
                    const SizedBox(height: 20),
                  ],

                  // Primary Bottom Submit Button (Hidden when failure card with contextual retry is visible)
                  if (!isReportSavedAndFailed) ...[
                    SizedBox(
                      height: 52,
                      child: FilledButton(
                        style: FilledButton.styleFrom(
                          backgroundColor: theme.colorScheme.primary,
                          foregroundColor: Colors.white,
                          disabledBackgroundColor: theme.colorScheme.onSurface.withValues(alpha: 0.12),
                          disabledForegroundColor: theme.colorScheme.onSurface.withValues(alpha: 0.30),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        onPressed: (isProcessing || _selectedFile == null) ? null : _uploadAndAnalyze,
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            if (isProcessing) ...[
                              const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white),
                              ),
                              const SizedBox(width: 12),
                            ],
                            Text(
                              isProcessing ? _processingStatusText : 'Upload & Analyze',
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(ThemeData theme, AppLocalizations? loc) {
    return Column(
      children: [
        Container(
          width: 72,
          height: 72,
          decoration: BoxDecoration(
            color: theme.colorScheme.primary.withValues(alpha: 0.10),
            shape: BoxShape.circle,
            border: Border.all(color: theme.colorScheme.primary.withValues(alpha: 0.20), width: 1.5),
          ),
          child: Icon(Icons.cloud_upload_outlined, color: theme.colorScheme.primary, size: 36),
        ),
        const SizedBox(height: 16),
        Text(
          loc?.uploadMedicalReport ?? 'Upload Medical Report',
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: theme.colorScheme.onSurface),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        Text(
          'PDF, JPG, JPEG, or PNG · Max 25 MB',
          style: TextStyle(color: theme.colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 13),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildReportTypeDropdown(ThemeData theme) {
    return DropdownButtonFormField<String>(
      initialValue: _reportType,
      dropdownColor: theme.cardColor,
      style: TextStyle(color: theme.colorScheme.onSurface),
      decoration: _inputDec('Report Type', Icons.category_outlined),
      items: _reportTypes
          .map((t) => DropdownMenuItem(
                value: t,
                child: Text(Helpers.reportTypeLabel(t), style: TextStyle(color: theme.colorScheme.onSurface)),
              ))
          .toList(),
      onChanged: (v) => setState(() => _reportType = v!),
    );
  }

  Widget _buildDatePickerTile(ThemeData theme) {
    final dateDisplay = _customDateSelected && _reportDate != null
        ? Formatters.formatDate(_reportDate!)
        : 'Auto-detect from document';

    return GestureDetector(
      onTap: () async {
        final picked = await showDatePicker(
          context: context,
          initialDate: _reportDate ?? DateTime.now(),
          firstDate: DateTime(2000),
          lastDate: DateTime.now(),
        );
        if (picked != null) {
          setState(() {
            _reportDate = picked;
            _customDateSelected = true;
          });
        }
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 15),
        decoration: BoxDecoration(
          color: theme.cardColor,
          border: Border.all(color: AppColors.border),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: [
            Icon(Icons.calendar_today_outlined, color: theme.colorScheme.onSurface.withValues(alpha: 0.54), size: 20),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Report Date', style: TextStyle(fontSize: 11, color: theme.colorScheme.onSurface.withValues(alpha: 0.60))),
                  const SizedBox(height: 2),
                  Text(
                    dateDisplay,
                    style: TextStyle(
                      color: _customDateSelected ? theme.colorScheme.onSurface : theme.colorScheme.onSurface.withValues(alpha: 0.75),
                      fontSize: 14,
                      fontWeight: _customDateSelected ? FontWeight.w600 : FontWeight.normal,
                    ),
                  ),
                ],
              ),
            ),
            if (_customDateSelected)
              IconButton(
                icon: const Icon(Icons.close_rounded, size: 18),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
                onPressed: () {
                  setState(() {
                    _reportDate = null;
                    _customDateSelected = false;
                  });
                },
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildFileArea(ThemeData theme) {
    if (_selectedFile == null) {
      return GestureDetector(
        onTap: _pickFile,
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: theme.cardColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: theme.colorScheme.primary.withValues(alpha: 0.40), width: 1.5),
          ),
          child: Column(
            children: [
              Icon(Icons.attach_file_rounded, color: theme.colorScheme.primary, size: 32),
              const SizedBox(height: 10),
              Text(
                'Choose a file to analyze',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: theme.colorScheme.onSurface),
              ),
              const SizedBox(height: 4),
              Text(
                'Supports PDF, JPG, JPEG, PNG (up to 25 MB)',
                style: TextStyle(fontSize: 12, color: theme.colorScheme.onSurface.withValues(alpha: 0.54)),
              ),
            ],
          ),
        ),
      );
    }

    final ext = _selectedFile!.extension?.toLowerCase() ?? '';
    final isPdf = ext == 'pdf';
    final isReportUploaded = _createdReportId != null;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: (isReportUploaded ? Colors.green : theme.colorScheme.primary).withValues(alpha: 0.50),
          width: 1.5,
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: (isPdf ? Colors.redAccent : Colors.blueAccent).withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              isPdf ? Icons.picture_as_pdf_rounded : Icons.image_rounded,
              color: isPdf ? Colors.redAccent : Colors.blueAccent,
              size: 28,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _selectedFile!.name,
                  style: TextStyle(color: theme.colorScheme.onSurface, fontWeight: FontWeight.bold, fontSize: 14),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(
                      Formatters.formatFileSize(_selectedFile!.size),
                      style: TextStyle(color: theme.colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 12),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.green.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        isReportUploaded ? 'Report uploaded' : 'File Ready',
                        style: const TextStyle(color: Colors.green, fontSize: 10, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close_rounded, color: Colors.grey),
            onPressed: _clearFile,
            tooltip: 'Remove file',
          ),
        ],
      ),
    );
  }

  Widget _buildUploadStatusIndicator(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Expanded(
            child: Row(
              children: [
                const Icon(Icons.check_circle_rounded, color: Colors.green, size: 18),
                const SizedBox(width: 6),
                Flexible(
                  child: Text(
                    'Step 1: Upload Completed',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: theme.colorScheme.onSurface),
                  ),
                ),
              ],
            ),
          ),
          Container(height: 20, width: 1, color: AppColors.border),
          const SizedBox(width: 12),
          Expanded(
            child: Row(
              children: [
                Icon(
                  _step == UploadStep.failed ? Icons.warning_amber_rounded : Icons.hourglass_empty_rounded,
                  color: _step == UploadStep.failed ? Colors.amber.shade800 : theme.colorScheme.primary,
                  size: 18,
                ),
                const SizedBox(width: 6),
                Flexible(
                  child: Text(
                    _step == UploadStep.failed
                        ? ((_failureCategory ?? '').contains('OCR') ||
                                (_failureCategory ?? '').contains('IMAGE') ||
                                (_failureCategory ?? '').contains('PDF') ||
                                (_failureCategory ?? '').contains('FILE')
                            ? 'Step 2: Text Extraction Failed'
                            : 'Step 2: AI Analysis Unavailable')
                        : 'Step 2: Processing AI Analysis',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: _step == UploadStep.failed ? Colors.amber.shade800 : theme.colorScheme.primary,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProcessingCard(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: theme.colorScheme.primary.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: theme.colorScheme.primary.withValues(alpha: 0.15)),
      ),
      child: Column(
        children: [
          Shimmer.fromColors(
            baseColor: theme.colorScheme.primary,
            highlightColor: theme.colorScheme.primary.withValues(alpha: 0.3),
            child: Icon(Icons.document_scanner_rounded, size: 48, color: theme.colorScheme.primary),
          ),
          const SizedBox(height: 20),
          Text(
            _processingStatusText,
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: theme.colorScheme.onSurface),
          ),
          const SizedBox(height: 8),
          Text(
            'This usually takes 10–20 seconds. Please wait...',
            style: TextStyle(fontSize: 13, color: theme.colorScheme.onSurface.withValues(alpha: 0.60)),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildErrorCard(ThemeData theme) {
    final isProcessing = _step == UploadStep.uploading || _step == UploadStep.processing;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.amber.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.amber.withValues(alpha: 0.40)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.warning_amber_rounded, color: Colors.amber, size: 24),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _failureCategory == 'OCR_ENGINE_UNAVAILABLE'
                      ? 'Text Recognition Unavailable'
                      : (_failureCategory == 'OCR_NO_MEANINGFUL_TEXT' ||
                              _failureCategory == 'OCR_FAILED' ||
                              _failureCategory == 'IMAGE_DECODE_ERROR'
                          ? 'Unable to Read This Image'
                          : (_failureCategory == 'PDF_EXTRACTION_ERROR' || _failureCategory == 'CORRUPT_PDF'
                              ? 'Unable to Read This Document'
                              : 'AI Analysis Unavailable')),
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: theme.colorScheme.onSurface),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            _errorMessage!,
            style: TextStyle(fontSize: 13, color: theme.colorScheme.onSurface.withValues(alpha: 0.85), height: 1.35),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 12,
            runSpacing: 10,
            children: [
              if (_createdReportId != null)
                FilledButton.icon(
                  onPressed: isProcessing ? null : _retryAnalysis,
                  icon: const Icon(Icons.refresh_rounded, size: 18),
                  label: const Text('Retry AI Analysis'),
                  style: FilledButton.styleFrom(
                    backgroundColor: theme.colorScheme.primary,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
              OutlinedButton.icon(
                onPressed: isProcessing ? null : _clearFile,
                icon: const Icon(Icons.upload_file_rounded, size: 18),
                label: const Text('Upload Another Report'),
                style: OutlinedButton.styleFrom(
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  InputDecoration _inputDec(String label, IconData icon, {String? hint}) => InputDecoration(
        labelText: label,
        hintText: hint,
        labelStyle: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
        hintStyle: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.35)),
        prefixIcon: Icon(icon, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)),
        filled: true,
        fillColor: Theme.of(context).cardColor,
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: Theme.of(context).colorScheme.onSurface, width: 1.5),
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