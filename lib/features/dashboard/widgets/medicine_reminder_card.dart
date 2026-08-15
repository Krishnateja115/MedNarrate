import 'package:flutter/material.dart';


class MedicineReminderCard extends StatelessWidget {
  const MedicineReminderCard({super.key});

  @override
  Widget build(BuildContext context) {

    return Container(

      width: double.infinity,

      padding: const EdgeInsets.all(22),

      decoration: BoxDecoration(

        color: Theme.of(context).cardColor,

        borderRadius: BorderRadius.circular(22),

      ),

      child: Row(

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
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70),
                  ),
                ),

                SizedBox(height: 5),

                Text(
                  "Paracetamol 650 mg",
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface,
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