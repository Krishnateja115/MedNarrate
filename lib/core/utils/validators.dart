import '../l10n/app_l10n.dart';

/// Validators — mirrors backend validation rules exactly.
/// Messages follow the language the user picked in the app.
class Validators {
  Validators._();

  static final RegExp _emailRegex = RegExp(
    r'^[\w\-\.]+@[\w\-]+\.[a-z]{2,}$',
    caseSensitive: false,
  );

  /// Returns null if the email is valid, otherwise an error message.
  static String? isValidEmail(String? value) {
    if (value == null || value.trim().isEmpty) return appL10n.emailRequired;
    if (!_emailRegex.hasMatch(value.trim())) return appL10n.emailInvalid;
    return null;
  }

  /// Returns null if the password meets backend requirements (≥8 chars, ≥1 letter, ≥1 digit).
  /// Returns a user-facing error message otherwise.
  static String? passwordStrengthError(String? value) {
    if (value == null || value.isEmpty) return appL10n.passwordIsRequired;
    if (value.length < 8) return appL10n.passwordMin8;
    if (!RegExp(r'[a-zA-Z]').hasMatch(value)) return appL10n.passwordNeedsLetter;
    if (!RegExp(r'\d').hasMatch(value)) return appL10n.passwordNeedsDigit;
    return null;
  }

  /// Returns null if the field is non-empty, otherwise an error message.
  static String? requiredField(String? value, {String? fieldName}) {
    if (value == null || value.trim().isEmpty) return appL10n.fieldRequired(fieldName ?? appL10n.thisField);
    return null;
  }
}
