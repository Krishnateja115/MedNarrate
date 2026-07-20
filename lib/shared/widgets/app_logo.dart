import 'package:flutter/material.dart';

import '../../core/constants/app_colors.dart';

class AppLogo extends StatelessWidget {
  final double size;

  const AppLogo({
    super.key,
    this.size = 90,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: size,
      width: size,

      decoration: BoxDecoration(
        color: AppColors.primary,
        borderRadius: BorderRadius.circular(size * .28),
      ),

      child: Icon(
        Icons.medical_services_rounded,
        size: size * .55,
        color: Colors.white,
      ),
    );
  }
}