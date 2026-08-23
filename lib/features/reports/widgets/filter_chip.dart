import 'package:flutter/material.dart';


class ReportsFilterChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback? onTap;

  const ReportsFilterChip({
    super.key,
    required this.label,
    required this.selected,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 10),
      child: FilterChip(
        label: Text(
          label,
          style: TextStyle(
            color: selected
                ? Colors.white
                : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70),
            fontWeight: FontWeight.w600,
          ),
        ),
        selected: selected,
        onSelected: (_) => onTap?.call(),
        backgroundColor: Theme.of(context).cardColor,
        selectedColor: Theme.of(context).colorScheme.primary,
        checkmarkColor: Colors.white,
        side: BorderSide.none,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(25),
        ),
        padding: const EdgeInsets.symmetric(
          horizontal: 12,
          vertical: 8,
        ),
      ),
    );
  }
}