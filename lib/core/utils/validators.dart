/// Validators — mirrors backend validation rules exactly.
class Validators {
  Validators._();

  static final RegExp _emailRegex = RegExp(
    r'^[\w\-\.]+@[\w\-]+\.[a-z]{2,}$',
    caseSensitive: false,
  );

  /// Returns null if the email is valid, otherwise an error message.
  static String? isValidEmail(String? value) {
    if (value == null || value.trim().isEmpty) return 'Email is required';
    if (!_emailRegex.hasMatch(value.trim())) return 'Enter a valid email address';
    return null;
  }

  /// Returns null if the password meets backend requirements (≥8 chars, ≥1 letter, ≥1 digit).
  /// Returns a user-facing error message otherwise.
  static String? passwordStrengthError(String? value) {
    if (value == null || value.isEmpty) return 'Password is required';
    if (value.length < 8) return 'Password must be at least 8 characters';
    if (!RegExp(r'[a-zA-Z]').hasMatch(value)) return 'Password must contain a letter';
    if (!RegExp(r'\d').hasMatch(value)) return 'Password must contain a digit';
    return null;
  }

  /// Returns null if the field is non-empty, otherwise an error message.
  static String? requiredField(String? value, {String fieldName = 'This field'}) {
    if (value == null || value.trim().isEmpty) return '$fieldName is required';
    return null;
  }
}
