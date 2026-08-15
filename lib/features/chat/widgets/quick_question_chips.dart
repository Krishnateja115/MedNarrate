import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';

class QuickQuestionChips extends StatelessWidget {
  final Function(String) onSelect;

  const QuickQuestionChips({super.key, required this.onSelect});

  static const List<String> questions = [
    "Summarize my results",
    "What values are abnormal?",
    "Is anything urgent?",
    "What should I ask my doctor?",
  ];

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: questions.map((q) {
          return Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: ActionChip(
              label: Text(q, style: TextStyle(color: AppColors.primary, fontSize: 13)),
              backgroundColor: AppColors.primary.withValues(alpha: 0.1),
              side: BorderSide.none,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              onPressed: () => onSelect(q),
            ),
          );
        }).toList(),
      ),
    );
  }
}
