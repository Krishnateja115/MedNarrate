import 'package:flutter/material.dart';


class HealthTipCard extends StatelessWidget {
  const HealthTipCard({super.key});

  @override
  Widget build(BuildContext context) {
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

              Icon(
                Icons.lightbulb_outline,
                color: Colors.white,
              ),

              SizedBox(width: 10),

              Text(
                "Today's Health Tip",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 19,
                  fontWeight: FontWeight.bold,
                ),
              ),

            ],
          ),

          SizedBox(height: 18),

          Text(
            "Drink enough water after taking morning medicines and avoid skipping breakfast.",
            style: TextStyle(
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