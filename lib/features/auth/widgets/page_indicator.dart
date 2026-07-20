import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class PageIndicator extends StatelessWidget {

  final bool active;

  const PageIndicator({
    super.key,
    required this.active,
  });

  @override
  Widget build(BuildContext context) {

    return AnimatedContainer(

      duration: const Duration(milliseconds: 300),

      margin: const EdgeInsets.symmetric(horizontal: 5),

      width: active ? 34 : 10,

      height: 10,

      decoration: BoxDecoration(
        color: active
            ? AppColors.primary
            : Colors.grey.shade700,

        borderRadius: BorderRadius.circular(20),
      ),
    );
  }
}