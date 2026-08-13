import 'package:flutter/material.dart';

import '../../core/constants/app_colors.dart';

class CustomPasswordField extends StatefulWidget {
  final TextEditingController controller;
  final String label;
  final String? Function(String?)? validator;

  const CustomPasswordField({
    super.key,
    required this.controller,
    required this.label,
    this.validator,
  });

  @override
  State<CustomPasswordField> createState() =>
      _CustomPasswordFieldState();
}

class _CustomPasswordFieldState
    extends State<CustomPasswordField> {

  bool obscure = true;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      validator: widget.validator,
      controller: widget.controller,
      obscureText: obscure,

      style: const TextStyle(
        color: Colors.white,
      ),

      decoration: InputDecoration(
        filled: true,
        fillColor: AppColors.card,

        prefixIcon: const Icon(
          Icons.lock_outline,
          color: AppColors.primary,
        ),

        suffixIcon: IconButton(
          onPressed: () {
            setState(() {
              obscure = !obscure;
            });
          },
          icon: Icon(
            obscure
                ? Icons.visibility_off
                : Icons.visibility,
          ),
        ),

        labelText: widget.label,

        labelStyle: const TextStyle(
          color: AppColors.textSecondary,
        ),

        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide.none,
        ),

        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(
            color: AppColors.primary,
            width: 2,
          ),
        ),
      ),
    );
  }
}