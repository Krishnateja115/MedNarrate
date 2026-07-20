import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

class DarkTheme {
  static ThemeData get theme {
    return ThemeData(
      useMaterial3: true,

      brightness: Brightness.dark,

      scaffoldBackgroundColor: AppColors.background,

      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        brightness: Brightness.dark,
      ),

      fontFamily: "Inter",

      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.background,
        centerTitle: false,
        elevation: 0,
      ),
    );
  }
}