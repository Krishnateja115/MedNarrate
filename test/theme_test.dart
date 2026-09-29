import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/constants/app_colors.dart';
import 'package:mednarrate/core/theme/app_theme.dart';

void main() {
  group('MedNarrate themes', () {
    test('light mode uses the pure-white forest palette', () {
      final theme = AppTheme.lightTheme;

      expect(theme.brightness, Brightness.light);
      expect(theme.scaffoldBackgroundColor, AppColors.lightBase);
      expect(theme.colorScheme.primary, AppColors.lightPrimary);
      expect(theme.colorScheme.surface, AppColors.lightBase);
      expect(theme.colorScheme.outlineVariant, AppColors.light300);
    });

    test('dark mode uses near-black surfaces and the teal accent', () {
      final theme = AppTheme.darkTheme;

      expect(theme.brightness, Brightness.dark);
      expect(theme.scaffoldBackgroundColor, AppColors.darkBase);
      expect(theme.colorScheme.primary, AppColors.darkPrimary);
      expect(theme.colorScheme.surface, AppColors.dark100);
      expect(theme.colorScheme.outlineVariant, AppColors.dark300);
    });

    test('semantic colors stay separate from brand colors', () {
      expect(AppTheme.lightTheme.colorScheme.error, AppColors.error);
      expect(AppTheme.darkTheme.colorScheme.error, AppColors.errorDark);
      expect(AppColors.warning, isNot(AppColors.lightPrimary));
      expect(AppColors.success, isNot(AppColors.lightPrimary));
    });

    test('core controls share the approved rounded outline system', () {
      final light = AppTheme.lightTheme;
      final dark = AppTheme.darkTheme;
      final lightCard = light.cardTheme.shape! as RoundedRectangleBorder;
      final darkCard = dark.cardTheme.shape! as RoundedRectangleBorder;

      expect(lightCard.borderRadius, BorderRadius.circular(16));
      expect(darkCard.borderRadius, BorderRadius.circular(16));
      expect(lightCard.side.color, AppColors.light300);
      expect(darkCard.side.color, AppColors.dark300);
    });
  });
}
