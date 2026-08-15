import 'package:flutter/material.dart';
import '../services/api_exception.dart';

sealed class AppError {
  final String message;
  AppError(this.message);
}

class NetworkError extends AppError {
  NetworkError(String message) : super(message);
}

class AuthError extends AppError {
  AuthError(String message) : super(message);
}

class ServerError extends AppError {
  ServerError(String message) : super(message);
}

class UnknownError extends AppError {
  UnknownError(String message) : super(message);
}

class ErrorHandler {
  static AppError parseError(dynamic error) {
    if (error is ApiException) {
      if (error.statusCode == 401 || error.statusCode == 403) {
        return AuthError(error.message);
      } else if (error.statusCode >= 500) {
        return ServerError(error.message);
      } else if (error.statusCode == 0) {
        return NetworkError(error.message);
      } else {
        return UnknownError(error.message);
      }
    }
    return UnknownError(error.toString());
  }

  static void showSnackBar(BuildContext context, dynamic error) {
    final appError = parseError(error);
    Color bgColor = Colors.red;
    if (appError is NetworkError) bgColor = Colors.amber.shade900;
    if (appError is AuthError) bgColor = Colors.orange;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(appError.message),
        backgroundColor: bgColor,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}
