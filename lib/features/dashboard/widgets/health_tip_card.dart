import 'package:flutter/material.dart';

import '../../../core/services/health_tip_service.dart';

class HealthTipCard extends StatelessWidget {
  const HealthTipCard({super.key});

  @override
  Widget build(BuildContext context) {
    // Deterministic: same local calendar date always returns the same tip.
    final todaysTip = HealthTipService.instance.getTodaysTip();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.green.shade700,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.lightbulb_outline,
                color: Colors.white,
              ),
              const SizedBox(width: 10),
              const Text(
                "Today's Health Tip",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 19,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          Text(
            todaysTip,
            style: const TextStyle(
              color: Colors.white,
              height: 1.5,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }
}