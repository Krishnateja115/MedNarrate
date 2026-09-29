import 'package:flutter/material.dart';

import '../constants/app_colors.dart';

class DarkTheme {
  static ThemeData get theme {
    const colorScheme = ColorScheme.dark(
      primary: AppColors.darkPrimary,
      onPrimary: Color(0xFF032019),
      primaryContainer: AppColors.darkPrimarySoft,
      onPrimaryContainer: Color(0xFF9DEBDA),
      secondary: AppColors.darkSecondary,
      onSecondary: Color(0xFF05221C),
      secondaryContainer: Color(0xFF15372F),
      onSecondaryContainer: Color(0xFFA9EEDF),
      surface: AppColors.dark100,
      onSurface: AppColors.dark950,
      surfaceContainerLowest: AppColors.darkBase,
      surfaceContainerLow: AppColors.dark50,
      surfaceContainer: AppColors.dark100,
      surfaceContainerHigh: AppColors.dark200,
      surfaceContainerHighest: AppColors.dark200,
      outline: AppColors.dark400,
      outlineVariant: AppColors.dark300,
      error: AppColors.errorDark,
      onError: Color(0xFF2D0808),
    );

    final textTheme = ThemeData.dark()
        .textTheme
        .apply(
          bodyColor: AppColors.dark950,
          displayColor: AppColors.dark950,
        )
        .copyWith(
          bodyMedium: const TextStyle(color: AppColors.dark700),
          bodySmall: const TextStyle(color: AppColors.dark500),
          titleLarge: const TextStyle(fontWeight: FontWeight.w700),
          titleMedium: const TextStyle(fontWeight: FontWeight.w600),
          labelLarge: const TextStyle(fontWeight: FontWeight.w600),
        );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: AppColors.darkBase,
      canvasColor: AppColors.darkBase,
      cardColor: AppColors.dark100,
      dividerColor: AppColors.dark300,
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.darkBase,
        foregroundColor: AppColors.dark950,
        surfaceTintColor: Colors.transparent,
        centerTitle: false,
        elevation: 0,
        scrolledUnderElevation: 0,
        titleTextStyle: textTheme.titleLarge?.copyWith(
          color: AppColors.dark950,
          fontSize: 20,
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.dark100,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.dark300),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.darkPrimary,
          foregroundColor: const Color(0xFF032019),
          disabledBackgroundColor: AppColors.dark200,
          disabledForegroundColor: AppColors.dark500,
          minimumSize: const Size(48, 50),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.darkPrimary,
          foregroundColor: const Color(0xFF032019),
          elevation: 0,
          surfaceTintColor: Colors.transparent,
          minimumSize: const Size(48, 50),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.darkPrimary,
          side: const BorderSide(color: AppColors.dark300),
          minimumSize: const Size(48, 50),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.darkPrimary,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: AppColors.darkPrimary,
        foregroundColor: Color(0xFF032019),
        elevation: 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(16)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.dark100,
        prefixIconColor: AppColors.dark500,
        suffixIconColor: AppColors.dark500,
        hintStyle: const TextStyle(color: AppColors.dark500),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 15,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.dark300),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.dark300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(
            color: AppColors.darkPrimary,
            width: 1.5,
          ),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.errorDark),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: AppColors.dark100,
        selectedColor: AppColors.darkPrimarySoft,
        disabledColor: AppColors.dark100,
        side: const BorderSide(color: AppColors.dark300),
        labelStyle: const TextStyle(color: AppColors.dark700),
        secondaryLabelStyle: const TextStyle(
          color: AppColors.darkPrimary,
          fontWeight: FontWeight.w600,
        ),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.dark300,
        space: 1,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.dark100,
        selectedItemColor: AppColors.darkPrimary,
        unselectedItemColor: AppColors.dark500,
        elevation: 0,
        type: BottomNavigationBarType.fixed,
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: AppColors.dark100,
        surfaceTintColor: Colors.transparent,
        indicatorColor: AppColors.darkPrimarySoft,
        elevation: 0,
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => TextStyle(
            color: states.contains(WidgetState.selected)
                ? AppColors.darkPrimary
                : AppColors.dark500,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w600
                : FontWeight.w500,
          ),
        ),
      ),
      tabBarTheme: const TabBarThemeData(
        labelColor: AppColors.darkPrimary,
        unselectedLabelColor: AppColors.dark500,
        indicatorColor: AppColors.darkPrimary,
        dividerColor: AppColors.dark300,
        indicatorSize: TabBarIndicatorSize.tab,
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: AppColors.dark100,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: AppColors.dark100,
        surfaceTintColor: Colors.transparent,
        modalBackgroundColor: AppColors.dark100,
        modalBarrierColor: Color(0xB3000000),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        showDragHandle: true,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? const Color(0xFF032019)
              : AppColors.dark500,
        ),
        trackColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? AppColors.darkPrimary
              : AppColors.dark200,
        ),
        trackOutlineColor: const WidgetStatePropertyAll(Colors.transparent),
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: AppColors.darkPrimary,
        linearTrackColor: AppColors.dark200,
        circularTrackColor: AppColors.dark200,
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.dark200,
        contentTextStyle: const TextStyle(color: AppColors.dark950),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
      iconTheme: const IconThemeData(color: AppColors.dark700),
      listTileTheme: const ListTileThemeData(
        iconColor: AppColors.dark600,
        textColor: AppColors.dark950,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(14)),
        ),
      ),
    );
  }
}
