import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,

      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        centerTitle: false,
        title: const Text(
          "Profile",
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),

        child: Column(
          children: [

            //--------------------------------------------------
            // PROFILE HEADER
            //--------------------------------------------------

            const CircleAvatar(
              radius: 52,
              backgroundColor: AppColors.primary,
              child: Icon(
                Icons.person,
                color: Colors.white,
                size: 55,
              ),
            ),

            const SizedBox(height: 18),

            const Text(
              "Krishna",
              style: TextStyle(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 6),

            const Text(
              "krishna@email.com",
              style: TextStyle(
                color: Colors.white70,
                fontSize: 16,
              ),
            ),

            const SizedBox(height: 35),

            //--------------------------------------------------
            // ACCOUNT
            //--------------------------------------------------

            _sectionTitle("Account"),

            const SizedBox(height: 15),

            _profileTile(
              Icons.person_outline,
              "Personal Information",
              "View and edit your personal details",
            ),

            _profileTile(
              Icons.medical_information_outlined,
              "Medical Information",
              "Blood group, allergies and history",
            ),

            _profileTile(
              Icons.emergency_outlined,
              "Emergency Contact",
              "Emergency contact information",
            ),

            const SizedBox(height: 30),

            //--------------------------------------------------
            // APP
            //--------------------------------------------------

            _sectionTitle("Application"),

            const SizedBox(height: 15),

            _profileTile(
              Icons.notifications_none,
              "Notifications",
              "Medicine reminders & alerts",
            ),

            _profileTile(
              Icons.dark_mode_outlined,
              "Appearance",
              "Light / Dark Theme",
            ),

            _profileTile(
              Icons.security_outlined,
              "Privacy & Security",
              "Manage your account security",
            ),

            _profileTile(
              Icons.help_outline,
              "Help & Support",
              "FAQs and contact support",
            ),

            _profileTile(
              Icons.info_outline,
              "About MedNarrate",
              "Version 1.0.0",
            ),

            const SizedBox(height: 35),

            SizedBox(
              width: double.infinity,
              height: 55,

              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(18),
                  ),
                ),

                onPressed: () {},

                icon: const Icon(
                  Icons.logout,
                  color: Colors.white,
                ),

                label: const Text(
                  "Logout",
                  style: TextStyle(
                    fontSize: 18,
                    color: Colors.white,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 30),

          ],
        ),
      ),
    );
  }

  Widget _sectionTitle(String title) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(
        title,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 22,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _profileTile(
    IconData icon,
    String title,
    String subtitle,
  ) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),

      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(20),
      ),

      child: Row(
        children: [

          CircleAvatar(
            radius: 24,
            backgroundColor: AppColors.primary.withValues(alpha: .15),
            child: Icon(
              icon,
              color: AppColors.primary,
            ),
          ),

          const SizedBox(width: 18),

          Expanded(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,

              children: [

                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 17,
                  ),
                ),

                const SizedBox(height: 5),

                Text(
                  subtitle,
                  style: const TextStyle(
                    color: Colors.white60,
                    fontSize: 14,
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