// Exception type used by all API calls.
// UI code only ever needs to catch ApiException.
class ApiException implements Exception {
  final int statusCode;
  final String message;

  const ApiException(this.statusCode, this.message);

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class UnauthorizedException extends ApiException {
  const UnauthorizedException() : super(401, 'Session expired. Please log in again.');
}
