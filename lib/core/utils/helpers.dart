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

  /// Checks whether a parameter name is patient/report metadata
  /// (e.g., PID, Sample Type, Collection Date) rather than a lab test.
  static bool isMetadataParameter(String name) {
    final lower = name.toLowerCase().trim();
    if (lower.isEmpty) return false;
    const metadataKeywords = [
      'pid',
      'patient id',
      'patient name',
      'sample type',
      'specimen type',
      'collection date',
      'report date',
      'referred by',
      'referral',
      'phone',
      'phone no',
      'mobile',
      'age/gender',
      'age / gender',
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
      'patient age',
      'report no',
      'report number',
      'barcode',
      'accession',
      'collected on',
      'received on',
      'reported on',
      'registration',
      'reg no',
      'name',
    ];
    return metadataKeywords.any(
      (kw) => lower == kw || lower.startsWith('$kw ') || lower.startsWith('$kw:'),
    );
  }

  /// Sanitises text for PDF rendering:
  /// - removes markdown heading markers (###, ##, #)
  /// - removes inline markdown symbols (**, *, __, _)
  /// - strips <INPUT_TEXT> block content and similar artifacts
  /// - removes entity group labels like (Diagnostic_procedure)
  /// - replaces non-WinAnsi glyphs (bullet chars, emoji, curly quotes)
  /// - strips any remaining non-Latin-1 characters to prevent PdfException
  static String sanitizePdfText(String text) {
    if (text.isEmpty) return '';
    var s = text;

    // 1. Strip <INPUT_TEXT>…</INPUT_TEXT> including content
    s = s.replaceAll(
        RegExp(r'<INPUT_TEXT>.*?</INPUT_TEXT>', dotAll: true), '');
    // Also remove naked tags in case the content was already stripped
    s = s.replaceAll('<INPUT_TEXT>', '').replaceAll('</INPUT_TEXT>', '');

    // 2. Strip common end-of-report markers
    s = s.replaceAll(RegExp(r'\*{0,4}End of Report\*{0,4}', caseSensitive: false), '');
    s = s.replaceAll(RegExp(r'###END.*?###', caseSensitive: false), '');

    // 3. Strip markdown heading markers (multiline)
    s = s.replaceAll(RegExp(r'^#+\s*', multiLine: true), '');

    // 4. Strip inline markdown symbols (bold/italic/code)
    s = s.replaceAll('**', '').replaceAll('__', '');
    // Single * only when flanking non-space (avoid breaking decimals)
    s = s.replaceAll(RegExp(r'(?<=\s)\*(?=\S)|\*(?=\s)'), '');
    // Single _ (italics) - strip when surrounding words
    s = s.replaceAll(RegExp(r'\b_([^_]+)_\b'), r'$1');

    // 5. Strip entity group labels like (Diagnostic_procedure), (Lab_value)
    s = s.replaceAll(RegExp(r'\([A-Za-z][A-Za-z_]*\)'), '');

    // 6. Replace emoji/non-WinAnsi glyphs with safe ASCII equivalents
    const Map<String, String> glyphMap = {
      '\u2022': '-',   // bullet •
      '\u00b7': '-',   // middle dot ·
      '\u2013': '-',   // en dash –
      '\u2014': '-',   // em dash —
      '\u201c': '"',   // left double quote
      '\u201d': '"',   // right double quote
      '\u2018': "'",   // left single quote
      '\u2019': "'",   // right single quote
      '\u2026': '...', // ellipsis
      '\u00ae': '(R)',
      '\u00a9': '(C)',
      '\u2122': '(TM)',
      '\u00b0': ' degrees',
      '\u00b5': 'u',
      '\u03b1': 'alpha',
      '\u03b2': 'beta',
      '\u03b3': 'gamma',
      '\u25a1': '-', // □ white square
      '\u25a0': '-', // ■ black square
      '\u2610': '-', // ☐ ballot box
    };
    for (final entry in glyphMap.entries) {
      s = s.replaceAll(entry.key, entry.value);
    }

    // 7. Strip all remaining non-WinAnsi / non-printable characters
    //    Keep: tab, LF, CR, printable ASCII (0x20-0x7E), extended Latin-1 (0xA0-0xFF)
    s = s.replaceAll(RegExp(r'[^\x09\x0A\x0D\x20-\x7E\xA0-\xFF]'), '');

    // 8. Collapse triple+ blank lines to double
    s = s.replaceAll(RegExp(r'\n{3,}'), '\n\n');

    return s.trim();
  }

  /// Sanitises text for on-screen Flutter display:
  /// - removes <INPUT_TEXT> artifacts
  /// - removes raw entity labels
  /// Emoji are allowed in Flutter UI, so we don't strip them here.
  static String sanitizeDisplayText(String text) {
    if (text.isEmpty) return '';
    var s = text;
    s = s.replaceAll(
        RegExp(r'<INPUT_TEXT>.*?</INPUT_TEXT>', dotAll: true), '');
    s = s.replaceAll('<INPUT_TEXT>', '').replaceAll('</INPUT_TEXT>', '');
    s = s.replaceAll(
        RegExp(r'\*{0,4}End of Report\*{0,4}', caseSensitive: false), '');
    s = s.replaceAll(RegExp(r'###END.*?###', caseSensitive: false), '');
    s = s.replaceAll(RegExp(r'\([A-Za-z][A-Za-z_]*\)'), '');
    s = s.replaceAll(RegExp(r'\n{3,}'), '\n\n');
    return s.trim();
  }
}
