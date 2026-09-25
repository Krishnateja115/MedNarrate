import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

import 'package:google_fonts/google_fonts.dart';

class DarkTheme {
  static ThemeData get theme {
    final baseTheme = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.darkBase,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.primary, // Purple Accent
        secondary: AppColors.secondary,
        surface: AppColors.dark100,
        surfaceContainerHighest: AppColors.dark200,
        onSurface: AppColors.dark950,
        error: AppColors.error,
      ),
      // Removed global fontFamily: "Inter" as it breaks Material Icons in Web HTML renderer
      textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme).copyWith(
        bodyLarge: const TextStyle(color: AppColors.dark950),
        bodyMedium: const TextStyle(color: AppColors.dark700),
        bodySmall: const TextStyle(color: AppColors.dark500),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.darkBase,
        foregroundColor: AppColors.dark950,
        centerTitle: false,
        elevation: 0,
        titleTextStyle: TextStyle(
          color: AppColors.dark950,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          disabledBackgroundColor: AppColors.dark300,
          disabledForegroundColor: AppColors.dark500,
          textStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.dark300,
        space: 1,
      ),
      cardTheme: CardThemeData(
        color: AppColors.dark100,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.dark200, width: 1),
        ),
      ),

      iconTheme: const IconThemeData(
        color: AppColors.primary, // Purple icons
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.dark100,
        prefixIconColor: AppColors.dark500,
        suffixIconColor: AppColors.dark500,
        hintStyle: const TextStyle(color: AppColors.dark500),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.dark300),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.dark300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.primary),
        ),
      ),
    );
    return baseTheme;
  }
}