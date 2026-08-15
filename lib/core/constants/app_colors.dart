import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  // Monochrome Light
  static const Color lightBase = Color(0xFFFFFFFF);
  static const Color light50 = Color(0xFFFAFAFA);
  static const Color light100 = Color(0xFFF5F5F5);
  static const Color light200 = Color(0xFFE5E5E5);
  static const Color light300 = Color(0xFFD4D4D4);
  static const Color light400 = Color(0xFFA3A3A3);
  static const Color light500 = Color(0xFF737373);
  static const Color light600 = Color(0xFF525252);
  static const Color light700 = Color(0xFF404040);
  static const Color light800 = Color(0xFF262626);
  static const Color light900 = Color(0xFF171717);
  static const Color light950 = Color(0xFF0A0A0A);

  // Monochrome Dark
  static const Color darkBase = Color(0xFF000000);
  static const Color dark50 = Color(0xFF0A0A0A);
  static const Color dark100 = Color(0xFF171717);
  static const Color dark200 = Color(0xFF262626);
  static const Color dark300 = Color(0xFF373737);
  static const Color dark400 = Color(0xFF525252);
  static const Color dark500 = Color(0xFF8A8A8A);
  static const Color dark600 = Color(0xFFA3A3A3);
  static const Color dark700 = Color(0xFFD4D4D4);
  static const Color dark800 = Color(0xFFE5E5E5);
  static const Color dark900 = Color(0xFFF5F5F5);
  static const Color dark950 = Color(0xFFFAFAFA);

  // Premium Primary & Accents (The purple accents the user requested)
  static const Color primary = Color(0xFF4C67F5); // Deep Indigo/Purple
  static const Color secondary = Color(0xFF8FA1FF); // Soft Periwinkle

  // Aliases for compatibility
  static const Color background = darkBase;
  static const Color surface = dark100;
  static const Color card = dark100;

  static const Color success = Color(0xFF267C3A);
  static const Color warning = Color(0xFF9A5F04);
  static const Color error = Color(0xFF993C3F);

  static const Color textPrimary = light950;
  static const Color textSecondary = light500;
  static const Color textHint = light400;

  static const Color divider = dark200;
  static const Color border = dark300;

  static const Color accentGold = Color(0xFFB89B27);
  static const Color accentTeal = Color(0xFF5D9BA5);

  static const Color white = Colors.white;
  static const Color black = Colors.black;
}