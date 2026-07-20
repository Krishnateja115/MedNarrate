import 'package:flutter/material.dart';

class InsightsScreen extends StatelessWidget {
  const InsightsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF151B2F),

      appBar: AppBar(
        backgroundColor: const Color(0xFF151B2F),
        elevation: 0,
        title: const Text(
          "Health Insights",
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      body: ListView(
        padding: const EdgeInsets.all(20),

        children: [

          _insightCard(
            Icons.favorite,
            Colors.red,
            "Heart Health",
            "Normal",
          ),

          const SizedBox(height: 18),

          _insightCard(
            Icons.water_drop,
            Colors.blue,
            "Blood Sugar",
            "Within Range",
          ),

          const SizedBox(height: 18),

          _insightCard(
            Icons.monitor_heart,
            Colors.green,
            "Cholesterol",
            "Healthy",
          ),

          const SizedBox(height: 18),

          _insightCard(
            Icons.medical_services,
            Colors.orange,
            "AI Summary",
            "No major health risks detected.",
          ),

        ],
      ),
    );
  }

  Widget _insightCard(
    IconData icon,
    Color color,
    String title,
    String value,
  ) {
    return Container(
      padding: const EdgeInsets.all(18),

      decoration: BoxDecoration(
        color: const Color(0xFF252C42),
        borderRadius: BorderRadius.circular(18),
      ),

      child: Row(
        children: [

          CircleAvatar(
            radius: 26,
            backgroundColor: color,
            child: Icon(
              icon,
              color: Colors.white,
            ),
          ),

          const SizedBox(width: 18),

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

                const SizedBox(height: 6),

                Text(
                  value,
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 15,
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