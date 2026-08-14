import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

class PrimaryButton extends StatefulWidget {
  final String text;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool loading;

  const PrimaryButton({
    super.key,
    required this.text,
    this.onPressed,
    this.icon,
    this.loading = false,
  });

  @override
  State<PrimaryButton> createState() => _PrimaryButtonState();
}

class _PrimaryButtonState extends State<PrimaryButton> {

  double scale = 1;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) {
        if (widget.onPressed == null || widget.loading) return;
        setState(() {
          scale = 0.97;
        });
      },
      onTapUp: (_) {
        if (widget.onPressed == null || widget.loading) return;
        setState(() {
          scale = 1;
        });

        widget.onPressed!();
      },
      onTapCancel: () {
        if (widget.onPressed == null || widget.loading) return;
        setState(() {
          scale = 1;
        });
      },
      child: AnimatedScale(
        scale: scale,
        duration: const Duration(milliseconds: 120),
        curve: Curves.easeOut,

        child: Container(
          height: 58,

          decoration: BoxDecoration(
            color: AppColors.primary,

            borderRadius: BorderRadius.circular(20),

            boxShadow: [
              BoxShadow(
                color: AppColors.primary.withValues(alpha: 0.20),
                blurRadius: 18,
                offset: const Offset(0, 8),
              ),
            ],
          ),

          child: Center(
            child: widget.loading
                ? const CircularProgressIndicator(
                    color: Colors.black,
                  )
                : Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [

                      if (widget.icon != null)
                        Icon(
                          widget.icon,
                          color: Colors.black,
                        ),

                      if (widget.icon != null)
                        const SizedBox(width: 10),

                      Text(
                        widget.text,
                        style: const TextStyle(
                          color: Colors.black,
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
          ),
        ),
      ),
    );
  }
}