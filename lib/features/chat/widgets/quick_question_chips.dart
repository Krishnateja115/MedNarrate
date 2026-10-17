import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/l10n/app_l10n.dart';

class QuickQuestionChips extends StatelessWidget {
  final Function(String) onSelect;

  const QuickQuestionChips({super.key, required this.onSelect});

  /// The four starter questions in the language the user picked.
  static List<String> get questions => [
        appL10n.quickSummarize,
        appL10n.quickAbnormal,
        appL10n.quickUrgent,
        appL10n.quickAskDoctor,
      ];

  /// Starter questions for the general assistant (no report open).
  static List<String> get generalQuestions => [
        appL10n.chatSuggestWorkout,
        appL10n.chatSuggestDiet,
        appL10n.chatSuggestSleep,
        appL10n.chatSuggestTerms,
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
              label: Text(q,
                  style: TextStyle(color: AppColors.primary, fontSize: 13)),
              backgroundColor: AppColors.primary.withValues(alpha: 0.1),
              side: BorderSide.none,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16)),
              onPressed: () => onSelect(q),
            ),
          );
        }).toList(),
      ),
    );
  }
}
