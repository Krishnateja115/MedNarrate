import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class DashboardStatisticsCard extends StatelessWidget {

  final String title;

  final String value;

  final IconData icon;

  final Color color;

  const DashboardStatisticsCard({

    super.key,

    required this.title,

    required this.value,

    required this.icon,

    required this.color,

  });

  @override
  Widget build(BuildContext context) {

    return Expanded(

      child: Container(

        padding: const EdgeInsets.all(18),

        decoration: BoxDecoration(

          color: AppColors.card,

          borderRadius: BorderRadius.circular(22),

        ),

        child: Column(

          children: [

            CircleAvatar(

              radius: 26,

              backgroundColor: color,

              child: Icon(

                icon,

                color: Colors.white,

              ),

            ),

            const SizedBox(height: 15),

            Text(

              value,

              style: const TextStyle(

                color: Colors.white,

                fontWeight: FontWeight.bold,

                fontSize: 24,

              ),

            ),

            const SizedBox(height: 5),

            Text(

              title,

              textAlign: TextAlign.center,

              style: const TextStyle(

                color: Colors.white60,

              ),

            ),

          ],

        ),

      ),

    );

  }

}