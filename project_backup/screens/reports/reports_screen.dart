import 'package:flutter/material.dart';

class ReportsScreen extends StatelessWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF151B2F),

      appBar: AppBar(
        backgroundColor: const Color(0xFF151B2F),
        elevation: 0,
        title: const Text(
          "Reports",
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      body: ListView(
        padding: const EdgeInsets.all(20),

        children: [

          _reportCard(
            "Blood Test",
            "Apollo Diagnostic Centre",
            "15 Jul 2026",
            Icons.bloodtype,
          ),

          _reportCard(
            "Lipid Profile",
            "City Health Labs",
            "10 Jul 2026",
            Icons.monitor_heart,
          ),

          _reportCard(
            "HbA1c Report",
            "MedPlus Diagnostics",
            "04 Jul 2026",
            Icons.health_and_safety,
          ),

        ],
      ),
    );
  }

  Widget _reportCard(
    String title,
    String hospital,
    String date,
    IconData icon,
  ) {
    return Container(
      margin: const EdgeInsets.only(bottom: 18),
      padding: const EdgeInsets.all(18),

      decoration: BoxDecoration(
        color: const Color(0xFF252C42),
        borderRadius: BorderRadius.circular(18),
      ),

      child: Row(
        children: [

          CircleAvatar(
            radius: 26,
            backgroundColor: const Color(0xFF4F6BFF),
            child: Icon(
              icon,
              color: Colors.white,
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
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                const SizedBox(height: 4),

                Text(
                  hospital,
                  style: const TextStyle(
                    color: Colors.white60,
                  ),
                ),

                const SizedBox(height: 6),

                Text(
                  date,
                  style: const TextStyle(
                    color: Colors.white38,
                    fontSize: 13,
                  ),
                ),

              ],
            ),
          ),

          const Icon(
            Icons.arrow_forward_ios,
            color: Colors.white54,
            size: 18,
          ),

        ],
      ),
    );
  }
}