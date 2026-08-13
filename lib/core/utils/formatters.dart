import 'package:intl/intl.dart';

class Formatters {
  Formatters._();

  static final DateFormat _dateFmt = DateFormat('MMM dd, yyyy');
  static final DateFormat _timeFmt = DateFormat('hh:mm a');

  /// Formats a [DateTime] as "Jan 01, 2025"
  static String formatDate(DateTime dt) => _dateFmt.format(dt);

  /// Formats a [DateTime] as "09:30 AM"
  static String formatTime(DateTime dt) => _timeFmt.format(dt);

  /// Formats bytes as "x.x MB", "x KB", etc.
  static String formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  /// Returns a short month-year label, e.g. "Aug 2025"
  static String formatMonthYear(DateTime dt) => DateFormat('MMM yyyy').format(dt);
}
