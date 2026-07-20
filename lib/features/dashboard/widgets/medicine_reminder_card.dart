import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class MedicineReminderCard extends StatelessWidget {
  const MedicineReminderCard({super.key});

  @override
  Widget build(BuildContext context) {

    return Container(

      width: double.infinity,

      padding: const EdgeInsets.all(22),

      decoration: BoxDecoration(

        color: AppColors.card,

        borderRadius: BorderRadius.circular(22),

      ),

      child: const Row(

        children: [

          CircleAvatar(
            radius: 28,
            backgroundColor: Colors.orange,
            child: Icon(
              Icons.medication,
              color: Colors.white,
            ),
          ),

          SizedBox(width: 18),

          Expanded(

            child: Column(

              crossAxisAlignment:
                  CrossAxisAlignment.start,

              children: [

                Text(
                  "Today's Medicine",
                  style: TextStyle(
                    color: Colors.white70,
                  ),
                ),

                SizedBox(height: 5),

                Text(
                  "Paracetamol 650 mg",
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),

                SizedBox(height: 4),

                Text(
                  "8:00 AM",
                  style: TextStyle(
                    color: Colors.orange,
                  ),
                ),

              ],
            ),
          )

        ],
      ),
    );
  }
}