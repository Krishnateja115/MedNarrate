import '../l10n/server_messages.dart';

// Exception type used by all API calls.
// UI code only ever needs to catch ApiException.
class ApiException implements Exception {
  final int statusCode;

  /// The message exactly as raised (English, from the app or the backend).
  /// Use for logging and comparisons; show [message] to the user.
  final String rawMessage;

  const ApiException(this.statusCode, this.rawMessage);

  /// User-facing text in the language the user picked. Messages that have no
  /// translation are shown unchanged.
  String get message => localizeApiMessage(rawMessage);

  @override
  String toString() => 'ApiException($statusCode): $rawMessage';
}

class UnauthorizedException extends ApiException {
  const UnauthorizedException() : super(401, 'Session expired. Please log in again.');
}
