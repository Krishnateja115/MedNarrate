import 'package:flutter/material.dart';

/// Extension methods available on common types app-wide.
extension StringExtensions on String {
  /// Capitalizes the first letter of each word.
  String toTitleCase() {
    return split(' ')
        .map((w) => w.isEmpty ? w : '${w[0].toUpperCase()}${w.substring(1)}')
        .join(' ');
  }

  /// Returns true if the string is a non-empty, non-whitespace-only string.
  bool get isNotBlank => trim().isNotEmpty;

  /// Truncates to [maxLength] and appends '…' if needed.
  String truncate(int maxLength) {
    if (length <= maxLength) return this;
    return '${substring(0, maxLength)}…';
  }
}

extension DateTimeExtensions on DateTime {
  /// Returns true if the date is today.
  bool get isToday {
    final now = DateTime.now();
    return year == now.year && month == now.month && day == now.day;
  }
}

extension ContextExtensions on BuildContext {
  /// Screen width.
  double get screenWidth => MediaQuery.of(this).size.width;

  /// Screen height.
  double get screenHeight => MediaQuery.of(this).size.height;

  /// True when the keyboard is visible.
  bool get isKeyboardOpen => MediaQuery.of(this).viewInsets.bottom > 0;
}
