import 'package:flutter/material.dart';

class AppTheme {
  static const Color background = Color(0xFF151B2F);
  static const Color card = Color(0xFF252C42);
  static const Color primary = Color(0xFF4F6BFF);
  static const Color accent = Color(0xFF69C3B2);
  static const Color text = Colors.white;
  static const Color subtitle = Color(0xFFB5BCD0);

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: background,

      colorScheme: ColorScheme.fromSeed(
        seedColor: primary,
        brightness: Brightness.dark,
      ),

      appBarTheme: const AppBarTheme(
        backgroundColor: background,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: text,
          fontSize: 30,
          fontWeight: FontWeight.bold,
        ),
      ),

      cardColor: card,

      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          color: text,
          fontWeight: FontWeight.bold,
        ),
        headlineMedium: TextStyle(
          color: text,
          fontWeight: FontWeight.bold,
        ),
        bodyLarge: TextStyle(
          color: text,
        ),
        bodyMedium: TextStyle(
          color: subtitle,
        ),
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, 55),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(15),
          ),
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: card,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(15),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }
}