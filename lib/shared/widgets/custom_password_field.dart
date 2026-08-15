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

      style: TextStyle(
        color: Theme.of(context).colorScheme.onSurface,
      ),

      decoration: InputDecoration(
        filled: true,
        fillColor: Theme.of(context).cardColor,

        prefixIcon: Icon(
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

        labelStyle: TextStyle(
          color: AppColors.textSecondary,
        ),

        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide.none,
        ),

        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide(
            color: AppColors.primary,
            width: 2,
          ),
        ),
      ),
    );
  }
}