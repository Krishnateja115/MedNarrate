import 'health_tips.dart';

/// Deterministic daily health-tip selector.
///
/// Algorithm:
///   dayIndex = daysSinceEpoch(today) % kHealthTips.length
///
/// This guarantees:
///   - The SAME calendar date always returns the SAME tip.
///   - Consecutive days ALWAYS return different tips.
///   - All 366 tips are cycled before any repeats (leap-year safe).
///   - No randomness, no network requests, works fully offline.
class HealthTipService {
  HealthTipService._();

  static final HealthTipService instance = HealthTipService._();

  /// Returns today's health tip based on the current local calendar date.
  ///
  /// The calculation is deterministic:
  ///   index = epoch_days_for_today % 366
  String getTodaysTip() => getTipForDate(DateTime.now());

  /// Returns the health tip for [date] (ignores time component).
  ///
  /// Exposed separately so unit tests can verify any date without mocking.
  String getTipForDate(DateTime date) {
    // Strip time — only year/month/day matters.
    final day = DateTime(date.year, date.month, date.day);
    // Reference epoch: 2000-01-01 (arbitrary, stable across platforms).
    final epoch = DateTime(2000, 1, 1);
    final daysSinceEpoch = day.difference(epoch).inDays;
    // Modulo handles both future and past dates safely.
    final index = daysSinceEpoch % kHealthTips.length;
    return kHealthTips[index];
  }

  /// The number of unique tips available.
  int get tipCount => kHealthTips.length;
}
