import 'package:intl/intl.dart';

class Formatters {
  Formatters._();

  static DateFormat _dateFmt(String locale) => DateFormat.yMMMd(locale);
  static DateFormat _timeFmt(String locale) => DateFormat.jm(locale);

  /// Formats a [DateTime] as "Jan 01, 2025" or localized equivalent
  static String formatDate(DateTime dt, [String locale = 'en']) => _dateFmt(locale).format(dt);

  /// Formats a [DateTime] as "09:30 AM" or localized equivalent
  static String formatTime(DateTime dt, [String locale = 'en']) => _timeFmt(locale).format(dt);

  /// Formats bytes as "x.x MB", "x KB", etc.
  static String formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  /// Returns a short month-year label, e.g. "Aug 2025"
  static String formatMonthYear(DateTime dt, [String locale = 'en']) => DateFormat.yMMM(locale).format(dt);
}
