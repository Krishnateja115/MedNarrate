import 'package:flutter/material.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

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
    if (score >= 80) return Color(0xFF00C48C);
    if (score >= 60) return Color(0xFFF5A623);
    return Color(0xFFE53935);
  }

  String _scoreLabel(BuildContext context) {
    if (totalLabValues == 0) return AppLocalizations.of(context)!.noLabDataYet;
    if (score >= 80) return AppLocalizations.of(context)!.scoreLookingGood;
    if (score >= 60) return AppLocalizations.of(context)!.scoreAttentionNeeded;
    return AppLocalizations.of(context)!.scoreConsultDoctor;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
            color: Theme.of(context).colorScheme.outlineVariant, width: 1),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  AppLocalizations.of(context)!.healthScore,
                  style: TextStyle(
                      color: Theme.of(context)
                          .colorScheme
                          .onSurface
                          .withValues(alpha: 0.70),
                      fontSize: 15),
                ),
                SizedBox(height: 6),
                totalLabValues == 0
                    ? Text(
                        '—',
                        style: TextStyle(
                            color: Theme.of(context)
                                .colorScheme
                                .onSurface
                                .withValues(alpha: 0.54),
                            fontSize: 36,
                            fontWeight: FontWeight.bold),
                      )
                    : Text(
                        '$score%',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onSurface,
                          fontSize: 42,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                SizedBox(height: 4),
                Text(
                  _scoreLabel(context),
                  style: TextStyle(
                      color: Theme.of(context)
                          .colorScheme
                          .onSurface
                          .withValues(alpha: 0.70),
                      fontSize: 13),
                ),
                if (totalLabValues > 0) ...[
                  SizedBox(height: 10),
                  Text(
                    AppLocalizations.of(context)!.abnormalOfTotal(abnormalCount, totalLabValues),
                    style: TextStyle(
                        color: Theme.of(context)
                            .colorScheme
                            .onSurface
                            .withValues(alpha: 0.60),
                        fontSize: 11),
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
                  backgroundColor: Theme.of(context)
                      .colorScheme
                      .primary
                      .withValues(alpha: 0.24),
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
