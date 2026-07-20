import 'package:flutter/material.dart';

class ReportCard extends StatelessWidget {
  final String title;
  final String hospital;
  final String date;

  const ReportCard({
    super.key,
    required this.title,
    required this.hospital,
    required this.date,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 15),
      padding: const EdgeInsets.all(18),

      decoration: BoxDecoration(
        color: const Color(0xFF252C42),
        borderRadius: BorderRadius.circular(18),
        boxShadow: const [
          BoxShadow(
            color: Colors.black26,
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),

      child: Row(
        children: [

          Container(
            padding: const EdgeInsets.all(14),

            decoration: BoxDecoration(
              color: const Color(0xFF4F6BFF),
              borderRadius: BorderRadius.circular(14),
            ),

            child: const Icon(
              Icons.description_outlined,
              color: Colors.white,
              size: 28,
            ),
          ),

          const SizedBox(width: 15),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [

                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                const SizedBox(height: 4),

                Text(
                  hospital,
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 14,
                  ),
                ),

                const SizedBox(height: 3),

                Text(
                  date,
                  style: const TextStyle(
                    color: Colors.white38,
                    fontSize: 12,
                  ),
                ),

              ],
            ),
          ),

          const Icon(
            Icons.arrow_forward_ios,
            color: Colors.white38,
            size: 18,
          ),

        ],
      ),
    );
  }
}