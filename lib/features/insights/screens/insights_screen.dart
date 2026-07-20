import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class InsightsScreen extends StatelessWidget {
  const InsightsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,

      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text(
          "Health Insights",
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),

        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,

          children: [

            //--------------------------------------------------------
            // HEALTH SCORE
            //--------------------------------------------------------

            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),

              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(24),
              ),

              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,

                children: [

                  Text(
                    "Overall Health Score",
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 18,
                    ),
                  ),

                  SizedBox(height: 12),

                  Text(
                    "92%",
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 42,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  SizedBox(height: 8),

                  Text(
                    "Your health indicators are looking good.",
                    style: TextStyle(
                      color: Colors.white,
                    ),
                  ),

                ],
              ),
            ),

            const SizedBox(height: 28),

            //--------------------------------------------------------
            // ABNORMAL VALUES
            //--------------------------------------------------------

            const Text(
              "Abnormal Findings",
              style: TextStyle(
                color: Colors.white,
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 16),

            _InsightCard(
              color: Colors.orange,
              icon: Icons.warning_amber_rounded,
              title: "High Cholesterol",
              subtitle:
                  "LDL cholesterol is slightly above the normal range.",
            ),

            _InsightCard(
              color: Colors.red,
              icon: Icons.favorite,
              title: "Blood Pressure",
              subtitle:
                  "Blood pressure should be monitored regularly.",
            ),

            const SizedBox(height: 28),

            //--------------------------------------------------------
            // RECOMMENDATIONS
            //--------------------------------------------------------

            const Text(
              "AI Recommendations",
              style: TextStyle(
                color: Colors.white,
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 16),

            _RecommendationTile(
              icon: Icons.restaurant,
              text: "Reduce saturated fat intake.",
            ),

            _RecommendationTile(
              icon: Icons.directions_walk,
              text: "Walk at least 30 minutes daily.",
            ),

            _RecommendationTile(
              icon: Icons.water_drop,
              text: "Drink 2-3 litres of water every day.",
            ),

            _RecommendationTile(
              icon: Icons.bedtime,
              text: "Maintain 7-8 hours of sleep.",
            ),

            const SizedBox(height: 28),

            //--------------------------------------------------------
            // DISCLAIMER
            //--------------------------------------------------------

            Container(
              padding: const EdgeInsets.all(20),

              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(20),
              ),

              child: const Row(
                crossAxisAlignment: CrossAxisAlignment.start,

                children: [

                  Icon(
                    Icons.info_outline,
                    color: Colors.blue,
                  ),

                  SizedBox(width: 12),

                  Expanded(
                    child: Text(
                      "These insights are AI-assisted and should not replace professional medical advice. Always consult your doctor before making health decisions.",
                      style: TextStyle(
                        color: Colors.white70,
                        height: 1.5,
                      ),
                    ),
                  ),

                ],
              ),
            ),

            const SizedBox(height: 30),

          ],
        ),
      ),
    );
  }
}

class _InsightCard extends StatelessWidget {
  final Color color;
  final IconData icon;
  final String title;
  final String subtitle;

  const _InsightCard({
    required this.color,
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 15),
      padding: const EdgeInsets.all(18),

      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(20),
      ),

      child: Row(
        children: [

          CircleAvatar(
            radius: 24,
            backgroundColor: color.withValues(alpha: .18),

            child: Icon(
              icon,
              color: color,
            ),
          ),

          const SizedBox(width: 16),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,

              children: [

                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 17,
                  ),
                ),

                const SizedBox(height: 6),

                Text(
                  subtitle,
                  style: const TextStyle(
                    color: Colors.white70,
                    height: 1.4,
                  ),
                ),

              ],
            ),
          ),

        ],
      ),
    );
  }
}

class _RecommendationTile extends StatelessWidget {
  final IconData icon;
  final String text;

  const _RecommendationTile({
    required this.icon,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),

      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(18),
      ),

      child: Row(
        children: [

          Icon(
            icon,
            color: AppColors.primary,
          ),

          const SizedBox(width: 16),

          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
              ),
            ),
          ),

        ],
      ),
    );
  }
}