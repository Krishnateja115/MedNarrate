import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

/// HealthScoreCard — now accepts real computed data.
/// Score is computed as: (normal lab values / total lab values) * 100
/// Falls back to "No data yet" if score is null.
class HealthScoreCard extends StatelessWidget {
  final int score;
  final int totalLabValues;
  final int abnormalCount;

  const HealthScoreCard({
    super.key,
    required this.score,
    this.totalLabValues = 0,
    this.abnormalCount = 0,
  });

  Color get _scoreColor {
    if (score >= 80) return const Color(0xFF00C48C);
    if (score >= 60) return const Color(0xFFF5A623);
    return const Color(0xFFE53935);
  }

  String get _scoreLabel {
    if (totalLabValues == 0) return 'No lab data yet';
    if (score >= 80) return 'Looking Good';
    if (score >= 60) return 'Some Attention Needed';
    return 'Consult Your Doctor';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppColors.border, width: 1),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Health Score',
                  style: TextStyle(color: Colors.white70, fontSize: 15),
                ),
                const SizedBox(height: 6),
                totalLabValues == 0
                    ? const Text(
                        '—',
                        style: TextStyle(color: Colors.white54, fontSize: 36, fontWeight: FontWeight.bold),
                      )
                    : Text(
                        '$score%',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 42,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                const SizedBox(height: 4),
                Text(
                  _scoreLabel,
                  style: const TextStyle(color: Colors.white70, fontSize: 13),
                ),
                if (totalLabValues > 0) ...[
                  const SizedBox(height: 10),
                  Text(
                    '$abnormalCount abnormal / $totalLabValues total values',
                    style: const TextStyle(color: Colors.white60, fontSize: 11),
                  ),
                ],
              ],
            ),
          ),
          Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                width: 76,
                height: 76,
                child: CircularProgressIndicator(
                  value: totalLabValues == 0 ? 0 : score / 100,
                  backgroundColor: Colors.white24,
                  color: _scoreColor,
                  strokeWidth: 7,
                ),
              ),
              Icon(
                totalLabValues == 0 ? Icons.favorite_border : Icons.favorite,
                color: _scoreColor,
                size: 28,
              ),
            ],
          ),
        ],
      ),
    );
  }
}