import 'package:flutter/material.dart';


class HealthProgressCard extends StatelessWidget {

  const HealthProgressCard({super.key});

  @override
  Widget build(BuildContext context) {

    return Container(

      width: double.infinity,

      padding: const EdgeInsets.all(22),

      decoration: BoxDecoration(

        color: Theme.of(context).cardColor,

        borderRadius: BorderRadius.circular(22),

      ),

      child: Column(

        crossAxisAlignment: CrossAxisAlignment.start,

        children: [

          Text(

            "Weekly Health Progress",

            style: TextStyle(

              color: Theme.of(context).colorScheme.onSurface,

              fontSize: 20,

              fontWeight: FontWeight.bold,

            ),

          ),

          SizedBox(height: 18),

          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: .82,
              minHeight: 10,
            ),
          ),

          SizedBox(height: 15),

          Text(

            "Your health score has improved by 12% compared to last week.",

            style: TextStyle(

              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70),

              height: 1.5,

            ),

          ),

        ],

      ),

    );

  }

}