import 'package:flutter/material.dart';

/// MedNarrate's restrained clinical palette.
///
/// Theme-aware components should prefer `Theme.of(context).colorScheme`.
/// These constants remain available for custom painters and legacy widgets that
/// cannot read a [BuildContext].
class AppColors {
  AppColors._();

  // Light neutrals — the app canvas is intentionally pure white.
  static const Color lightBase = Color(0xFFFFFFFF);
  static const Color light50 = Color(0xFFFFFFFF);
  static const Color light100 = Color(0xFFF6F9F7);
  static const Color light200 = Color(0xFFE5ECE8);
  static const Color light300 = Color(0xFFD2DDD8);
  static const Color light400 = Color(0xFFA2B0AA);
  static const Color light500 = Color(0xFF6F7D77);
  static const Color light600 = Color(0xFF52615B);
  static const Color light700 = Color(0xFF38453F);
  static const Color light800 = Color(0xFF23302B);
  static const Color light900 = Color(0xFF17211D);
  static const Color light950 = Color(0xFF0E1713);

  // Dark neutrals — near-black surfaces retain depth without blue tint.
  static const Color darkBase = Color(0xFF050807);
  static const Color dark50 = Color(0xFF090D0B);
  static const Color dark100 = Color(0xFF111816);
  static const Color dark200 = Color(0xFF1A2421);
  static const Color dark300 = Color(0xFF2A3934);
  static const Color dark400 = Color(0xFF53635D);
  static const Color dark500 = Color(0xFF8D9B96);
  static const Color dark600 = Color(0xFFA8B4B0);
  static const Color dark700 = Color(0xFFC5CECA);
  static const Color dark800 = Color(0xFFDDE4E1);
  static const Color dark900 = Color(0xFFEEF3F1);
  static const Color dark950 = Color(0xFFF8FBFA);

  // ThemeData supplies the brighter accent automatically in dark mode.
  static const Color primary = Color(0xFF0B7563);
  static const Color lightPrimary = Color(0xFF0B6B5B);
  static const Color darkPrimary = Color(0xFF32CDB3);
  static const Color secondary = Color(0xFF198F7C);
  static const Color darkSecondary = Color(0xFF6EDBC8);
  static const Color primarySoft = Color(0xFFE8F4F0);
  static const Color darkPrimarySoft = Color(0xFF102A24);

  // Aliases retained for compatibility with existing feature code.
  static const Color background = darkBase;
  static const Color surface = dark100;
  static const Color card = dark100;

  // Semantic colors remain distinct from the brand color.
  static const Color success = Color(0xFF287A58);
  static const Color successDark = Color(0xFF65D6A3);
  static const Color warning = Color(0xFF9A6700);
  static const Color warningDark = Color(0xFFF3C969);
  static const Color error = Color(0xFFB33A3A);
  static const Color errorDark = Color(0xFFF08080);

  static const Color textPrimary = light950;
  static const Color textSecondary = light600;
  static const Color textHint = light500;

  // Prefer ColorScheme.outlineVariant for theme-aware borders.
  static const Color divider = light200;
  static const Color border = light300;

  static const Color accentGold = Color(0xFF9A6700);
  static const Color accentTeal = Color(0xFF20AD96);

  static const Color white = Colors.white;
  static const Color black = Colors.black;
}
