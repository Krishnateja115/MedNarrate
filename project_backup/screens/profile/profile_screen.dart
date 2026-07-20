import 'package:flutter/material.dart';
import 'personal_info_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF151B2F),

      appBar: AppBar(
        backgroundColor: const Color(0xFF151B2F),
        elevation: 0,
        title: const Text(
          "Profile",
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),

        child: Column(
          children: [

            const CircleAvatar(
              radius: 55,
              backgroundColor: Color(0xFF4F6BFF),
              child: Icon(
                Icons.person,
                color: Colors.white,
                size: 60,
              ),
            ),

            const SizedBox(height: 20),

            const Text(
              "Krishna",
              style: TextStyle(
                color: Colors.white,
                fontSize: 26,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 6),

            const Text(
              "21 Years • Male",
              style: TextStyle(
                color: Colors.white70,
                fontSize: 16,
              ),
            ),

            const SizedBox(height: 5),

            const Text(
              "krishna@email.com",
              style: TextStyle(
                color: Colors.white54,
                fontSize: 15,
              ),
            ),

            const SizedBox(height: 35),

            profileTile(
              context,
              Icons.person,
              "Personal Information",
              const PersonalInfoScreen(),
            ),

            profileTile(
              context,
              Icons.medical_services,
              "Medical Information",
              null,
            ),

            profileTile(
              context,
              Icons.phone,
              "Emergency Contact",
              null,
            ),

            profileTile(
              context,
              Icons.bar_chart,
              "Health Statistics",
              null,
            ),

            profileTile(
              context,
              Icons.settings,
              "Settings",
              null,
            ),

            profileTile(
              context,
              Icons.info_outline,
              "About MedNarrate",
              null,
            ),

            const SizedBox(height: 30),

            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.logout),
                label: const Text(
                  "Logout",
                  style: TextStyle(fontSize: 18),
                ),
              ),
            ),

          ],
        ),
      ),
    );
  }

  Widget profileTile(
    BuildContext context,
    IconData icon,
    String title,
    Widget? page,
  ) {
    return InkWell(
      borderRadius: BorderRadius.circular(18),

      onTap: () {
        if (page != null) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => page,
            ),
          );
        }
      },

      child: Container(
        margin: const EdgeInsets.only(bottom: 15),
        padding: const EdgeInsets.all(18),

        decoration: BoxDecoration(
          color: const Color(0xFF252C42),
          borderRadius: BorderRadius.circular(18),
        ),

        child: Row(
          children: [

            Icon(
              icon,
              color: Colors.white,
            ),

            const SizedBox(width: 18),

            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 17,
                ),
              ),
            ),

            const Icon(
              Icons.arrow_forward_ios,
              color: Colors.white38,
              size: 18,
            ),

          ],
        ),
      ),
    );
  }
}