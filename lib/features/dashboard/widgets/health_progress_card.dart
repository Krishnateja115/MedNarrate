import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class HealthProgressCard extends StatelessWidget {

  const HealthProgressCard({super.key});

  @override
  Widget build(BuildContext context) {

    return Container(

      width: double.infinity,

      padding: const EdgeInsets.all(22),

      decoration: BoxDecoration(

        color: AppColors.card,

        borderRadius: BorderRadius.circular(22),

      ),

      child: const Column(

        crossAxisAlignment: CrossAxisAlignment.start,

        children: [

          Text(

            "Weekly Health Progress",

            style: TextStyle(

              color: Colors.white,

              fontSize: 20,

              fontWeight: FontWeight.bold,

            ),

          ),

          SizedBox(height: 18),

          LinearProgressIndicator(

            value: .82,

            minHeight: 10,

          ),

          SizedBox(height: 15),

          Text(

            "Your health score has improved by 12% compared to last week.",

            style: TextStyle(

              color: Colors.white70,

              height: 1.5,

            ),

          ),

        ],

      ),

    );

  }

}