import 'package:flutter/material.dart';

class SnapshotCard extends StatelessWidget {
  final String number;
  final String title;
  final Color circleColor;

  const SnapshotCard({
    super.key,
    required this.number,
    required this.title,
    required this.circleColor,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 5),
        padding: const EdgeInsets.symmetric(vertical: 20),

        decoration: BoxDecoration(
          color: const Color(0xFF252C42),
          borderRadius: BorderRadius.circular(18),
          boxShadow: const [
            BoxShadow(
              color: Colors.black26,
              blurRadius: 8,
              offset: Offset(0, 4),
            ),
          ],
        ),

        child: Column(
          children: [

            CircleAvatar(
              radius: 28,
              backgroundColor: circleColor,

              child: Text(
                number,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),

            const SizedBox(height: 15),

            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
                fontSize: 15,
              ),
            ),

          ],
        ),
      ),
    );
  }
}