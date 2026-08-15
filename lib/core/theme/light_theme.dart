import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

class LightTheme {
  static ThemeData get theme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: AppColors.light50,
      colorScheme: const ColorScheme.light(
        primary: AppColors.primary, // Purple Accent
        secondary: AppColors.secondary,
        surface: AppColors.lightBase,
        surfaceContainerHighest: AppColors.light200,
        onSurface: AppColors.light950,
        error: AppColors.error,
      ),
      fontFamily: "Inter",
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.light50,
        foregroundColor: AppColors.light950,
        centerTitle: false,
        elevation: 0,
        titleTextStyle: TextStyle(
          color: AppColors.light950,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.primary, 
          foregroundColor: Colors.white,
          disabledBackgroundColor: AppColors.light300,
          disabledForegroundColor: AppColors.light500,
          textStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.light200,
        space: 1,
      ),
      cardTheme: CardThemeData(
        color: AppColors.lightBase,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.light200, width: 1),
        ),
      ),
      textTheme: const TextTheme(
        bodyLarge: TextStyle(color: AppColors.light950),
        bodyMedium: TextStyle(color: AppColors.light700),
        bodySmall: TextStyle(color: AppColors.light500),
      ),
      iconTheme: const IconThemeData(
        color: AppColors.primary, // Purple icons
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.lightBase,
        prefixIconColor: AppColors.light500,
        suffixIconColor: AppColors.light500,
        hintStyle: const TextStyle(color: AppColors.light500),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.light300),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.light300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.primary),
        ),
      ),
    );
  }
}