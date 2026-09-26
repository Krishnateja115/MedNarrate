import 'package:flutter/material.dart';

/// Miscellaneous helpers used across the app.
class Helpers {
  Helpers._();

  /// Shows a [SnackBar] with an error style.
  static void showError(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red.shade700,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  /// Shows a [SnackBar] with a success style.
  static void showSuccess(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green.shade700,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  /// Returns a user-friendly label for a report_type string.
  static String reportTypeLabel(String type) {
    switch (type) {
      case 'blood':
        return 'Blood Test';
      case 'pathology':
        return 'Pathology';
      case 'health':
        return 'Health Check';
      default:
        return 'Other';
    }
  }

  /// Maps a flag string to a color for lab value badges.
  static Color flagColor(String flag) {
    switch (flag.toLowerCase()) {
      case 'critical':
      case 'abnormal':
      case 'high':
        return Colors.red.shade600;
      case 'low':
      case 'moderate':
      case 'borderline':
        return Colors.orange.shade700;
      default:
        return Colors.green.shade600;
    }
  }

  /// Maps a processing_status to a user-friendly string.
  static String statusLabel(String status) {
    switch (status) {
      case 'uploaded':
        return 'Uploaded';
      case 'processing':
        return 'Analyzing…';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return status;
    }
  }

  /// Checks if a parameter name is patient/report metadata (e.g., PID, Sample Type) rather than a lab test.
  static bool isMetadataParameter(String name) {
    final lower = name.toLowerCase().trim();
    final metadataKeywords = [
      'pid',
      'patient id',
      'patient name',
      'sample type',
      'specimen type',
      'collection date',
      'report date',
      'referred by',
      'phone',
      'phone no',
      'mobile',
      'age/gender',
      'gender',
      'sex',
      'dob',
      'date of birth',
      'doctor',
      'physician',
      'hospital',
      'lab name',
      'laboratory',
      'address',
    ];
    return metadataKeywords.any((kw) => lower == kw || lower.startsWith('$kw ') || lower.startsWith('$kw:'));
  }

  /// Sanitizes text for PDF rendering by replacing non-Latin-1 glyphs and markdown artifacts.
  static String sanitizePdfText(String text) {
    if (text.isEmpty) return '';
    var s = text;
    // Replace markdown headings
    s = s.replaceAll(RegExp(r'^#+\s*', multiLine: true), '');
    // Replace raw markdown symbols
    s = s.replaceAll('**', '').replaceAll('*', '').replaceAll('__', '').replaceAll('_', '');
    // Replace input text tag artifacts
    s = s.replaceAll('<INPUT_TEXT>', '').replaceAll('</INPUT_TEXT>', '');
    s = s.replaceAll('****End of Report****', '');
    // Replace entity parentheses like (Diagnostic_procedure)
    s = s.replaceAll(RegExp(r'\([A-Za-z_]+\)'), '');
    // Replace common non-Latin1 bullet/symbol glyphs with clean ASCII
    s = s.replaceAll('•', '- ')
         .replaceAll('', '')
         .replaceAll('□', '-')
         .replaceAll('✓', '[OK]')
         .replaceAll('❌', '[X]')
         .replaceAll('·', '-')
         .replaceAll('–', '-')
         .replaceAll('—', '-')
         .replaceAll('“', '"')
         .replaceAll('”', '"')
         .replaceAll('’', "'")
         .replaceAll('‘', "'");
    
    // Strip any remaining non-WinAnsi / non-ASCII characters to avoid PdfException
    s = s.replaceAll(RegExp(r'[^\x09\x0A\x0D\x20-\x7E\xA0-\xFF]'), '');
    return s.trim();
  }
}
