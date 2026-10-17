import 'package:intl/intl.dart';

import '../l10n/locale_notifier.dart';

class Formatters {
  Formatters._();

  // With no explicit language, dates follow the language the user picked in the app.
  static String _lang(String? locale) =>
      locale ?? localeModeNotifier.value.languageCode;

  static DateFormat _dateFmt(String? locale) => DateFormat.yMMMd(_lang(locale));
  static DateFormat _timeFmt(String? locale) => DateFormat.jm(_lang(locale));

  /// Formats a [DateTime] as "Jan 01, 2025" or localized equivalent
  static String formatDate(DateTime dt, [String? locale]) => _dateFmt(locale).format(dt);

  /// Formats a [DateTime] as "09:30 AM" or localized equivalent
  static String formatTime(DateTime dt, [String? locale]) => _timeFmt(locale).format(dt);

  /// Formats bytes as "x.x MB", "x KB", etc.
  static String formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  /// Returns a short month-year label, e.g. "Aug 2025"
  static String formatMonthYear(DateTime dt, [String? locale]) =>
      DateFormat.yMMM(_lang(locale)).format(dt);
}
