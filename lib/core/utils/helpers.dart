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
    switch (flag) {
      case 'high':
        return Colors.red.shade600;
      case 'low':
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
}
